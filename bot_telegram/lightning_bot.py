import os
import psutil
import grpc
import time
import asyncio
import logging
import requests
from threading import Thread
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from lightning_pb2 import (
    GetInfoRequest, WalletBalanceRequest, ListChannelsRequest,
    ListInvoiceRequest, GetTransactionsRequest, InvoiceSubscription,
    ListPaymentsRequest, ForwardingHistoryRequest
)
from lightning_pb2_grpc import LightningStub
from datetime import datetime

# Configure the Telegram API token and chat ID
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# Configure the communication channel with LND
LND_DIR = os.getenv('LND_DIR', '/path/to/your/lnd/')  # Update with actual path if needed
CERT_PATH = os.path.join(LND_DIR, 'tls.cert')
MACAROON_PATH = os.path.join(LND_DIR, 'chain/bitcoin/mainnet/admin.macaroon')

# Configure logging
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

def get_bitcoin_price_and_fees():
    try:
        # Get Bitcoin price in USD and EUR
        coingecko_url = 'https://api.coingecko.com/api/v3/simple/price'
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'usd,eur',
            'include_market_cap': 'false',
            'include_24hr_vol': 'false',
            'include_24hr_change': 'false',
            'include_last_updated_at': 'true'
        }
        response = requests.get(coingecko_url, params=params)
        price_data = response.json()
        
        # Get network fees from Mempool
        mempool_url = 'https://mempool.space/api/v1/fees/recommended'
        response = requests.get(mempool_url)
        fees_data = response.json()
        
        btc_price_usd = price_data['bitcoin']['usd']
        btc_price_eur = price_data['bitcoin']['eur']
        fast_fee = fees_data['fastestFee']
        half_hour_fee = fees_data['halfHourFee']
        hour_fee = fees_data['hourFee']
        
        return (btc_price_usd, btc_price_eur, fast_fee, half_hour_fee, hour_fee)
    except Exception as e:
        logging.error(f"Error fetching Bitcoin price and fees: {e}")
        return (None, None, None, None, None)

async def start(update: Update, context):
    await show_menu(update)

async def menu(update: Update, context):
    await show_menu(update)

async def show_menu(update: Update):
    keyboard = [
        [InlineKeyboardButton("⚡ Node Info", callback_data='nodeinfo')],
        [InlineKeyboardButton("📊 Channel Info", callback_data='channelinfo')],
        [InlineKeyboardButton("🔄 Recent Transactions", callback_data='recenttransactions')],
        [InlineKeyboardButton("🔄 Forwarding Transactions", callback_data='forwardingtransactions')],
        [InlineKeyboardButton("₿ Bitcoin Info", callback_data='bitcoininfo')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('🤖 Bot is active! Select an option:', reply_markup=reply_markup)

async def button(update: Update, context):
    query = update.callback_query
    await query.answer()

    if query.data == 'nodeinfo':
        await get_node_info(query)
    elif query.data == 'channelinfo':
        await get_channel_info(query)
    elif query.data == 'recenttransactions':
        await get_recent_transactions(query)
    elif query.data == 'forwardingtransactions':
        await get_forwarding_transactions(query)
    elif query.data == 'bitcoininfo':
        await get_bitcoin_info(query)

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
        disk_info = psutil.disk_usage('/')  # Generic path
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
        await update.message.reply_text(f"Error retrieving node info: {e.details()}")

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
        await update.message.reply_text(f"Error retrieving channel info: {e.details()}")

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
            f"₿ You have {'received' if tx.amount >= 0 else 'paid'} {abs(tx.amount)} satoshis via an on-chain transaction.\n"
            f"   Date: {datetime.fromtimestamp(tx.time_stamp).strftime('%Y-%m-%d %H:%M:%S') if tx.time_stamp else 'Date not available'}"
            for tx in recent_onchain
        ])

        # Prepare Lightning transactions info
        lightning_transactions = "\n".join([
            f"⚡ You have {'received' if invoice.amt_paid_sat >= 0 else 'paid'} {abs(invoice.amt_paid_sat)} satoshis via a Lightning invoice.\n"
            f"   Memo: {invoice.memo}\n"
            f"   Date: {datetime.fromtimestamp(invoice.settle_date).strftime('%Y-%m-%d %H:%M:%S') if invoice.settle_date else 'Date not available'}"
            for invoice in recent_invoices
        ])

        # Prepare the response message
        text = "Recent Transactions:\n"
        text += onchain_transactions + "\n" if onchain_transactions else ""
        text += lightning_transactions + "\n" if lightning_transactions else ""

        await update.message.reply_text(text)
    except grpc.RpcError as e:
        logging.error(f"gRPC error while getting recent transactions: {e.details()}")
        await update.message.reply_text(f"Error retrieving recent transactions: {e.details()}")

async def get_forwarding_transactions(update):
    try:
        stub = get_ln_stub()
        response = stub.ForwardingHistory(ForwardingHistoryRequest())
        forwarding_info = "\n".join([
            f"⚡ Forwarded {tx.amt_in} satoshis to {tx.pub_key}.\n"
            f"   Fee: {tx.fee} satoshis\n"
            f"   Date: {datetime.fromtimestamp(tx.timestamp).strftime('%Y-%m-%d %H:%M:%S') if tx.timestamp else 'Date not available'}"
            for tx in response.forwarding_events
        ])
        await update.message.reply_text(f"Forwarding Transactions:\n{forwarding_info}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error while getting forwarding transactions: {e.details()}")
        await update.message.reply_text(f"Error retrieving forwarding transactions: {e.details()}")

async def get_bitcoin_info(update):
    try:
        btc_price_usd, btc_price_eur, fast_fee, half_hour_fee, hour_fee = get_bitcoin_price_and_fees()
        if btc_price_usd is not None:
            text = (f"💰 Bitcoin Price:\n"
                    f"   - USD: ${btc_price_usd}\n"
                    f"   - EUR: €{btc_price_eur}\n\n"
                    f"💸 Network Fees:\n"
                    f"   - Fastest Fee: {fast_fee} satoshis/byte\n"
                    f"   - Half Hour Fee: {half_hour_fee} satoshis/byte\n"
                    f"   - Hour Fee: {hour_fee} satoshis/byte")
            await update.message.reply_text(text)
        else:
            await update.message.reply_text("Error retrieving Bitcoin price and fees.")
    except Exception as e:
        logging.error(f"Error retrieving Bitcoin info: {e}")
        await update.message.reply_text(f"Error retrieving Bitcoin info: {e}")

def main():
    # Setup the Telegram bot
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))

    # Run the bot
    logging.info("Bot started.")
    application.run_polling()

if __name__ == '__main__':
    main()
