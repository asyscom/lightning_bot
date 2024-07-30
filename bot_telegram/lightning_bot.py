import os
import psutil
import grpc
import time
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from lightning_pb2 import (
    GetInfoRequest, WalletBalanceRequest, ListChannelsRequest,
    ListInvoiceRequest, GetTransactionsRequest, ClosedChannelsRequest,
    InvoiceSubscription
)
from lightning_pb2_grpc import LightningStub

# Configura il token API di Telegram
TELEGRAM_TOKEN = 'BOT_TOKEN'
CHAT_ID = 'CHAT_ID'

# Configura il canale di comunicazione con LND su RaspiBlitz
LND_DIR = '/mnt/hdd/app-data/lnd/'
CERT_PATH = os.path.join(LND_DIR, 'tls.cert')
MACAROON_PATH = os.path.join(LND_DIR, 'data/chain/bitcoin/mainnet/admin.macaroon')

def get_macaroon_hex():
    with open(MACAROON_PATH, 'rb') as f:
        macaroon_bytes = f.read()
    return macaroon_bytes.hex()

def get_ln_stub():
    with open(CERT_PATH, 'rb') as f:
        cert = f.read()
    creds = grpc.ssl_channel_credentials(cert)
    auth_creds = grpc.metadata_call_credentials(lambda context, callback: callback([('macaroon', get_macaroon_hex())], None))
    combined_creds = grpc.composite_channel_credentials(creds, auth_creds)
    channel = grpc.secure_channel('localhost:10009', combined_creds)
    return LightningStub(channel)

async def start(update: Update, context):
    keyboard = [
        [InlineKeyboardButton("⚡ Node Info", callback_data='nodeinfo')],
        [InlineKeyboardButton("📊 Channel Info", callback_data='channelinfo')],
        [InlineKeyboardButton("🔄 Recent Transactions", callback_data='recenttransactions')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🤖 Bot active! Select an option:', reply_markup=reply_markup)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'nodeinfo':
        await get_node_info(query)
    elif query.data == 'channelinfo':
        await get_channel_info(query)
    elif query.data == 'recenttransactions':
        await get_recent_transactions(query)

async def get_node_info(update):
    try:
        stub = get_ln_stub()
        
        # Get node info
        info_response = stub.GetInfo(GetInfoRequest())
        
        # Get wallet balance (on-chain)
        balance_response = stub.WalletBalance(WalletBalanceRequest())
        
        # Get channel balance (Lightning)
        channel_response = stub.ListChannels(ListChannelsRequest())
        lightning_balance = sum(channel.local_balance for channel in channel_response.channels)
        
        # Get system info
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/mnt/hdd')
        
        # Prepare the response message
        text = (f"⚡ Alias: {info_response.alias}\n"
                f"🛠️ Version: {info_response.version}\n"
                f"🔢 Block Height: {info_response.block_height}\n"
                f"💰 On-chain Balance: {balance_response.total_balance} satoshis\n"
                f"⚡ Lightning Balance: {lightning_balance} satoshis\n"
                f"🔗 Total Channels: {len(channel_response.channels)}\n"
                f"🖥️ CPU Usage: {cpu_usage}%\n"
                f"🧠 Free Memory: {memory_info.available / (1024 ** 2):.2f} MB\n"
                f"💾 Free Disk Space: {disk_info.free / (1024 ** 3):.2f} GB")
                
        await update.message.reply_text(text)
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le informazioni del nodo: {e.details()}")

async def get_channel_info(update):
    try:
        stub = get_ln_stub()
        response = stub.ListChannels(ListChannelsRequest())
        channels_info = "\n".join([
            f"📡 Channel with {channel.remote_pubkey}\n"
            f"   - Capacity: {channel.capacity} satoshis\n"
            f"   - Local Balance: {channel.local_balance} satoshis\n"
            f"   - Remote Balance: {channel.remote_balance} satoshis"
            for channel in response.channels
        ])
        await update.message.reply_text(f"📊 Channels:\n{channels_info}")
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le informazioni dei canali: {e.details()}")

async def get_recent_transactions(update):
    try:
        stub = get_ln_stub()

        # Fetch recent on-chain transactions
        response_onchain = stub.GetTransactions(GetTransactionsRequest())
        recent_onchain = response_onchain.transactions[-10:]  # Get the last 10 on-chain transactions
        
        # Fetch recent Lightning invoices
        response_invoices = stub.ListInvoices(ListInvoiceRequest(pending_only=False))
        recent_invoices = response_invoices.invoices[-10:]  # Get the last 10 invoices

        # Prepare on-chain transactions info
        onchain_transactions = "\n".join([
            f"🔄 On-chain Tx Hash: {tx.tx_hash}, Amount: {tx.amount} satoshis"
            for tx in recent_onchain
        ])

        # Prepare Lightning transactions info
        lightning_transactions = "\n".join([
            f"⚡ Lightning Invoice: {invoice.memo}, Amount: {invoice.value} satoshis"
            for invoice in recent_invoices
        ])

        # Prepare the response message
        text = "Recent Transactions:\n"
        text += onchain_transactions + "\n" if onchain_transactions else ""
        text += lightning_transactions + "\n" if lightning_transactions else ""

        await update.message.reply_text(text)
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le transazioni recenti: {e.details()}")

def monitor_onchain_transactions(bot):
    previous_tx_ids = set()
    while True:
        try:
            stub = get_ln_stub()
            response = stub.GetTransactions(GetTransactionsRequest())
            new_tx_ids = {tx.tx_hash for tx in response.transactions}

            for tx in response.transactions:
                if tx.tx_hash not in previous_tx_ids:
                    bot.send_message(chat_id=CHAT_ID, text=f"🔔 New On-chain Transaction: {tx.tx_hash} for {tx.amount} satoshis")

            previous_tx_ids = new_tx_ids
        except grpc.RpcError as e:
            bot.send_message(chat_id=CHAT_ID, text=f"Errore nel monitoraggio delle transazioni on-chain: {e.details()}")

        time.sleep(60)  # Adjust as needed

def monitor_lightning_invoices(bot):
    stub = get_ln_stub()
    for invoice in stub.SubscribeInvoices(InvoiceSubscription()):
        if invoice.settled:
            bot.send_message(chat_id=CHAT_ID, text=f"💰 Received a Lightning payment of {invoice.amt_paid_sat} satoshis. Memo: {invoice.memo}")

def monitor_channels(bot):
    previous_channels = None
    while True:
        try:
            stub = get_ln_stub()
            response = stub.ListChannels(ListChannelsRequest())
            current_channels = {channel.chan_id: channel.active for channel in response.channels}
            
            if previous_channels is not None:
                for chan_id, is_active in current_channels.items():
                    if chan_id in previous_channels and previous_channels[chan_id] and not is_active:
                        bot.send_message(chat_id=CHAT_ID, text=f"Channel with {chan_id} is now offline.")
            
            previous_channels = current_channels
            time.sleep(60)  # Controlla ogni 60 secondi
        except grpc.RpcError as e:
            bot.send_message(chat_id=CHAT_ID, text=f"Errore nel monitoraggio dei canali: {e.details()}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    bot = application.bot
    Thread(target=monitor_onchain_transactions, args=(bot,)).start()
    Thread(target=monitor_lightning_invoices, args=(bot,)).start()
    Thread(target=monitor_channels, args=(bot,)).start()

    application.run_polling()

if __name__ == "__main__":
    main()
