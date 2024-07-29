import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
import grpc
from lightning_pb2 import GetInfoRequest, WalletBalanceRequest, ListChannelsRequest, ListInvoiceRequest, GetTransactionsRequest, ClosedChannelsRequest
from lightning_pb2_grpc import LightningStub
import time
from threading import Thread

# Configura il token API di Telegram
TELEGRAM_TOKEN = 'TOKEN_BOT
CHAT_ID = 'YOUR CHAT ID'

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
        [InlineKeyboardButton("Node Info", callback_data='nodeinfo')],
        [InlineKeyboardButton("Wallet Balance", callback_data='walletbalance')],
        [InlineKeyboardButton("Channel Info", callback_data='channelinfo')],
        [InlineKeyboardButton("Pending Invoices", callback_data='pendinginvoices')],
        [InlineKeyboardButton("Recent Transactions", callback_data='recenttransactions')],
        [InlineKeyboardButton("Closed Channels", callback_data='notifychannelclosure')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Bot attivo! Seleziona un\'opzione:', reply_markup=reply_markup)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'nodeinfo':
        await get_node_info(query, context)
    elif query.data == 'walletbalance':
        await get_wallet_balance(query, context)
    elif query.data == 'channelinfo':
        await get_channel_info(query, context)
    elif query.data == 'pendinginvoices':
        await get_pending_invoices(query, context)
    elif query.data == 'recenttransactions':
        await get_recent_transactions(query, context)
    elif query.data == 'notifychannelclosure':
        await notify_channel_closure(query, context)

async def get_node_info(update: Update, context):
    stub = get_ln_stub()
    response = stub.GetInfo(GetInfoRequest())
    await update.message.reply_text(f"Alias: {response.alias}\nBlock Height: {response.block_height}")

async def get_wallet_balance(update: Update, context):
    stub = get_ln_stub()
    response = stub.WalletBalance(WalletBalanceRequest())
    await update.message.reply_text(f"Total Balance: {response.total_balance} satoshis\nConfirmed Balance: {response.confirmed_balance} satoshis")

async def get_channel_info(update: Update, context):
    stub = get_ln_stub()
    response = stub.ListChannels(ListChannelsRequest())
    channels_info = "\n".join([f"Channel ID: {channel.chan_id}, Capacity: {channel.capacity}, Local Balance: {channel.local_balance}" for channel in response.channels])
    await update.message.reply_text(f"Channels:\n{channels_info}")

async def get_pending_invoices(update: Update, context):
    stub = get_ln_stub()
    response = stub.ListInvoices(ListInvoiceRequest(pending_only=True))
    invoices_info = "\n".join([f"Invoice: {invoice.memo}, Amount: {invoice.value} satoshis" for invoice in response.invoices])
    await update.message.reply_text(f"Pending Invoices:\n{invoices_info}")

async def get_recent_transactions(update: Update, context):
    stub = get_ln_stub()
    response = stub.GetTransactions(GetTransactionsRequest())
    transactions_info = "\n".join([f"Tx Hash: {tx.tx_hash}, Amount: {tx.amount} satoshis" for tx in response.transactions])
    await update.message.reply_text(f"Recent Transactions:\n{transactions_info}")

async def notify_channel_closure(update: Update, context):
    stub = get_ln_stub()
    response = stub.ClosedChannels(ClosedChannelsRequest())
    closed_channels_info = "\n".join([f"Channel Point: {channel.channel_point}, Closing Tx: {channel.closing_tx_hash}" for channel in response.channels])
    await update.message.reply_text(f"Closed Channels:\n{closed_channels_info}")

def monitor_channels(bot):
    previous_channels = None
    while True:
        stub = get_ln_stub()
        response = stub.ListChannels(ListChannelsRequest())
        current_channels = {channel.chan_id: channel.active for channel in response.channels}
        
        if previous_channels is not None:
            for chan_id, is_active in current_channels.items():
                if chan_id in previous_channels and previous_channels[chan_id] and not is_active:
                    bot.send_message(chat_id=CHAT_ID, text=f"Channel {chan_id} is now offline.")
        
        previous_channels = current_channels
        time.sleep(60)  # Controlla ogni 60 secondi

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    
    bot = application.bot
    Thread(target=monitor_channels, args=(bot,)).start()

    application.run_polling()

if __name__ == "__main__":
    main()

