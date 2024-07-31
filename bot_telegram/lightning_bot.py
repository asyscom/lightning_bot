import os
import psutil
import grpc
import time
import asyncio
import logging
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from lightning_pb2 import (
    GetInfoRequest, WalletBalanceRequest, ListChannelsRequest,
    ListInvoiceRequest, GetTransactionsRequest, InvoiceSubscription,
    ListPaymentsRequest
)
from lightning_pb2_grpc import LightningStub

# Configura il token API di Telegram
TELEGRAM_TOKEN = 'TOKEN_API_BOT'
CHAT_ID = 'YUOR_CHAT_ID'

# Configura il canale di comunicazione con LND su RaspiBlitz
LND_DIR = '/mnt/hdd/app-data/lnd/'
CERT_PATH = os.path.join(LND_DIR, 'tls.cert')
MACAROON_PATH = os.path.join(LND_DIR, 'data/chain/bitcoin/mainnet/admin.macaroon')

# Configura il logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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

def get_cpu_temperature():
    try:
        # Read CPU temperature from thermal zone
        temp_files = [f"/sys/class/thermal/thermal_zone{i}/temp" for i in range(10)]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                with open(temp_file, 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return f"{temp:.1f}°C"
        return "Temperature sensor not found"
    except Exception as e:
        logging.error(f"Error reading CPU temperature: {e}")
        return "Error reading temperature"

async def start(update: Update, context):
    await show_menu(update)

async def menu(update: Update, context):
    await show_menu(update)

async def show_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("⚡ Node Info", callback_data='nodeinfo')],
        [InlineKeyboardButton("📊 Channel Info", callback_data='channelinfo')],
        [InlineKeyboardButton("🔄 Recent Transactions", callback_data='recenttransactions')],
        [InlineKeyboardButton("🔄 Routing Transactions", callback_data='routingtransactions')],
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
    elif query.data == 'routingtransactions':
        await get_routing_transactions(query)

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
        cpu_temperature = get_cpu_temperature()
        
        # Prepare the response message
        text = (f"⚡ Alias: {info_response.alias}\n"
                f"🛠️ Version: {info_response.version}\n"
                f"🔢 Block Height: {info_response.block_height}\n"
                f"💰 On-chain Balance: {balance_response.total_balance} satoshis\n"
                f"⚡ Lightning Balance: {lightning_balance} satoshis\n"
                f"🔗 Total Channels: {len(channel_response.channels)}\n"
                f"🖥️ CPU Usage: {cpu_usage}%\n"
                f"🧠 Free Memory: {memory_info.available / (1024 ** 2):.2f} MB\n"
                f"💾 Free Disk Space: {disk_info.free / (1024 ** 3):.2f} GB\n"
                f"🌡️ CPU Temperature: {cpu_temperature}")
                
        await update.message.reply_text(text)
    except grpc.RpcError as e:
        logging.error(f"gRPC error while getting node info: {e.details()}")
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
        logging.error(f"gRPC error while getting channel info: {e.details()}")
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
        logging.error(f"gRPC error while getting recent transactions: {e.details()}")
        await update.message.reply_text(f"Errore nel recuperare le transazioni recenti: {e.details()}")

async def get_routing_transactions(update):
    try:
        stub = get_ln_stub()
        response = stub.ListPayments(ListPaymentsRequest())
        routing_info = "\n".join([
            f"🔄 Payment Hash: {payment.payment_hash}\n"
            f"   - Amount: {payment.value} satoshis\n"
            f"   - Status: {payment.status}\n"
            f"   - Created: {payment.creation_date}"
            for payment in response.payments
        ])
        await update.message.reply_text(f"🔄 Routing Transactions:\n{routing_info}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error while getting routing transactions: {e.details()}")
        await update.message.reply_text(f"Errore nel recuperare le transazioni di routing: {e.details()}")

def monitor_onchain_transactions(application, loop):
    previous_tx_ids = set()
    while True:
        try:
            stub = get_ln_stub()
            response = stub.GetTransactions(GetTransactionsRequest())
            new_tx_ids = {tx.tx_hash for tx in response.transactions}

            for tx in response.transactions:
                if tx.tx_hash not in previous_tx_ids:
                    asyncio.run_coroutine_threadsafe(
                        application.bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"🔔 New On-chain Transaction: {tx.tx_hash} for {tx.amount} satoshis"
                        ),
                        loop
                    )

            previous_tx_ids = new_tx_ids
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring on-chain transactions: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Errore nel monitoraggio delle transazioni on-chain: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring on-chain transactions: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Errore imprevisto nel monitoraggio delle transazioni on-chain: {e}"
                ),
                loop
            )
        time.sleep(60)  # Adjust as needed

def monitor_lightning_invoices(application, loop):
    stub = get_ln_stub()
    for invoice in stub.SubscribeInvoices(InvoiceSubscription()):
        if invoice.settled:
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"💰 Received a Lightning payment of {invoice.amt_paid_sat} satoshis. Memo: {invoice.memo}"
                ),
                loop
            )

def monitor_channels(application, loop):
    previous_channels = None
    while True:
        try:
            stub = get_ln_stub()
            response = stub.ListChannels(ListChannelsRequest())
            current_channels = {channel.chan_id: channel.active for channel in response.channels}
            
            if previous_channels is not None:
                for chan_id, is_active in current_channels.items():
                    if chan_id in previous_channels and previous_channels[chan_id] and not is_active:
                        asyncio.run_coroutine_threadsafe(
                            application.bot.send_message(
                                chat_id=CHAT_ID,
                                text=f"Channel with {chan_id} is now offline."
                            ),
                            loop
                        )
            
            previous_channels = current_channels
            time.sleep(60)  # Check every 60 seconds
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring channels: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Errore nel monitoraggio dei canali: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring channels: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"Errore imprevisto nel monitoraggio dei canali: {e}"
                ),
                loop
            )
        time.sleep(60)  # Check every 60 seconds

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    loop = asyncio.get_event_loop()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', menu))  # Add menu command
    application.add_handler(CallbackQueryHandler(button))
    
    # Pass loop as argument to monitoring threads
    Thread(target=monitor_onchain_transactions, args=(application, loop)).start()
    Thread(target=monitor_lightning_invoices, args=(application, loop)).start()
    Thread(target=monitor_channels, args=(application, loop)).start()

    application.run_polling()

if __name__ == "__main__":
    main()
