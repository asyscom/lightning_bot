import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import grpc
from lightning_pb2 import (
    GetInfoRequest, WalletBalanceRequest, ListChannelsRequest,
    GetTransactionsRequest, ClosedChannelsRequest, InvoiceSubscription
)
from lightning_pb2_grpc import LightningStub
import time
from threading import Thread

# Configura il token API di Telegram
TELEGRAM_TOKEN = 'TOKEN_BOT'
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
    await update.message.reply_text('🤖 Bot attivo! Seleziona un\'opzione:', reply_markup=reply_markup)

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

        # Prepare the response message
        text = (f"⚡ Alias: {info_response.alias}\n"
                f"🛠️ Version: {info_response.version}\n"
                f"🔢 Block Height: {info_response.block_height}\n"
                f"💰 On-chain Balance: {balance_response.total_balance} satoshis\n"
                f"⚡ Lightning Balance: {lightning_balance} satoshis\n"
                f"🔗 Total Channels: {len(channel_response.channels)}")
                
        await update.message.reply_text(text)
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le informazioni del nodo: {e.details()}")

async def get_channel_info(update):
    try:
        stub = get_ln_stub()
        response = stub.ListChannels(ListChannelsRequest())
        channels_info = "\n".join([f"📡 Channel with {channel.remote_pubkey}, Capacity: {channel.capacity}, Local Balance: {channel.local_balance}" for channel in response.channels])
        await update.message.reply_text(f"📊 Channels:\n{channels_info}")
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le informazioni dei canali: {e.details()}")

async def get_recent_transactions(update):
    try:
        stub = get_ln_stub()
        response = stub.GetTransactions(GetTransactionsRequest())
        transactions_info = "\n".join([f"🔄 Tx Hash: {tx.tx_hash}, Amount: {tx.amount} satoshis" for tx in response.transactions])
        await update.message.reply_text(f"Recent Transactions:\n{transactions_info}")
    except grpc.RpcError as e:
        await update.message.reply_text(f"Errore nel recuperare le transazioni recenti: {e.details()}")

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
                        bot.send_message(chat_id=CHAT_ID, text=f"Channel with {response.remote_pubkey} is now offline.")
            
            previous_channels = current_channels
            time.sleep(60)  # Controlla ogni 60 secondi
        except grpc.RpcError as e:
            bot.send_message(chat_id=CHAT_ID, text=f"Errore nel monitoraggio dei canali: {e.details()}")

def monitor_invoices(bot):
    stub = get_ln_stub()
    for invoice in stub.SubscribeInvoices(InvoiceSubscription()):
        if invoice.settled:
            bot.send_message(chat_id=CHAT_ID, text=f"💰 Received a Lightning payment of {invoice.amt_paid_sat} satoshis. Memo: {invoice.memo}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    bot = application.bot
    Thread(target=monitor_channels, args=(bot,)).start()
    Thread(target=monitor_invoices, args=(bot,)).start()

    application.run_polling()

if __name__ == "__main__":
    main()
