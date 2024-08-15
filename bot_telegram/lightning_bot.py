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
    ListPaymentsRequest, ForwardingHistoryRequest
)
from lightning_pb2_grpc import LightningStub

# Configure Telegram API token
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', 'your_telegram_token')
CHAT_ID = os.getenv('CHAT_ID', 'your_chat_id')

# Configure communication with LND
LND_DIR = '/path/to/lnd/'
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
        [InlineKeyboardButton("🔄 Forwarding Transactions", callback_data='forwardingtransactions')],
        [InlineKeyboardButton("💸 Network Fees", callback_data='fees')]
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
    elif query.data == 'fees':
        await get_network_fees(query)

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
        disk_info = psutil.disk_usage('/')
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
        logging.error(f"gRPC error while retrieving node info: {e.details()}")
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
        logging.error(f"gRPC error while retrieving channel info: {e.details()}")
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
            f"🔄 On-chain Transaction Hash: {tx.tx_hash}, Amount: {tx.amount} satoshis"
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
        logging.error(f"gRPC error while retrieving recent transactions: {e.details()}")
        await update.message.reply_text(f"Error retrieving recent transactions: {e.details()}")

async def get_forwarding_transactions(update):
    try:
        stub = get_ln_stub()
        response = stub.ForwardingHistory(ForwardingHistoryRequest())
        forwarding_info = "\n".join([
            f"🔄 Forwarding Event:\n"
            f"   - Channel In: {event.chan_id_in}\n"
            f"   - Channel Out: {event.chan_id_out}\n"
            f"   - Amount: {event.amt_in} satoshis\n"
            f"   - Fee: {event.fee} satoshis\n"
            f"   - Timestamp: {event.timestamp}"
            for event in response.forwarding_events
        ])
        await update.message.reply_text(f"🔄 Forwarding Transactions:\n{forwarding_info}")
    except grpc.RpcError as e:
        logging.error(f"gRPC error while retrieving forwarding transactions: {e.details()}")
        await update.message.reply_text(f"Error retrieving forwarding transactions: {e.details()}")

async def get_network_fees(update):
    try:
        # Placeholder values for fee rates
        min_fee_sats_per_vbyte = 3
        max_fee_sats_per_vbyte = 10

        # Conversion rates (example values)
        btc_to_eur = 26000
        btc_to_usd = 28000

        min_fee_eur = min_fee_sats_per_vbyte * btc_to_eur / 1e8
        max_fee_eur = max_fee_sats_per_vbyte * btc_to_eur / 1e8
        min_fee_usd = min_fee_sats_per_vbyte * btc_to_usd / 1e8
        max_fee_usd = max_fee_sats_per_vbyte * btc_to_usd / 1e8

        text = (f"💸 Network Fees:\n"
                f"   - Minimum Fee: {min_fee_sats_per_vbyte} sat/vbyte\n"
                f"     - Equivalent in EUR: €{min_fee_eur:.2f}\n"
                f"     - Equivalent in USD: ${min_fee_usd:.2f}\n"
                f"   - Maximum Fee: {max_fee_sats_per_vbyte} sat/vbyte\n"
                f"     - Equivalent in EUR: €{max_fee_eur:.2f}\n"
                f"     - Equivalent in USD: ${max_fee_usd:.2f}")

        await update.message.reply_text(text)
    except Exception as e:
        logging.error(f"Error retrieving network fees: {e}")
        await update.message.reply_text(f"Error retrieving network fees: {e}")

def monitor_lightning_invoices(application, loop):
    stub = get_ln_stub()
    previous_invoices = set()
    for invoice in stub.SubscribeInvoices(InvoiceSubscription()):
        if invoice.settled:
            if invoice.r_hash not in previous_invoices:
                asyncio.run_coroutine_threadsafe(
                    application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=f"🔔 Lightning Invoice Received: {invoice.amt_paid_sat} satoshis\nMemo: {invoice.memo}"
                    ),
                    loop
                )
                previous_invoices.add(invoice.r_hash)

def monitor_lightning_transactions(application, loop):
    stub = get_ln_stub()
    previous_payments = set()
    while True:
        try:
            response = stub.ListPayments(ListPaymentsRequest())
            for payment in response.payments:
                if payment.payment_hash not in previous_payments:
                    asyncio.run_coroutine_threadsafe(
                        application.bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"🚀 Lightning Payment Sent: {payment.value} satoshis\nRecipient: {payment.payee}"
                        ),
                        loop
                    )
                    previous_payments.add(payment.payment_hash)
        
            time.sleep(60)  # Adjust as needed
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring Lightning transactions: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Error monitoring Lightning transactions: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring Lightning transactions: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Unexpected error monitoring Lightning transactions: {e}"
                ),
                loop
            )
        time.sleep(60)  # Check every 60 seconds

def monitor_onchain_transactions(application, loop):
    stub = get_ln_stub()
    previous_transactions = set()
    while True:
        try:
            response = stub.GetTransactions(GetTransactionsRequest())
            for tx in response.transactions:
                if tx.tx_hash not in previous_transactions:
                    asyncio.run_coroutine_threadsafe(
                        application.bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"🔄 On-chain Transaction: {tx.tx_hash}\nAmount: {tx.amount} satoshis"
                        ),
                        loop
                    )
                    previous_transactions.add(tx.tx_hash)
        
            time.sleep(60)  # Adjust as needed
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring on-chain transactions: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Error monitoring on-chain transactions: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring on-chain transactions: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Unexpected error monitoring on-chain transactions: {e}"
                ),
                loop
            )
        time.sleep(60)  # Check every 60 seconds

def monitor_channels(application, loop):
    stub = get_ln_stub()
    previous_channels = set()
    while True:
        try:
            response = stub.ListChannels(ListChannelsRequest())
            for channel in response.channels:
                if channel.chan_id not in previous_channels:
                    asyncio.run_coroutine_threadsafe(
                        application.bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"📡 New Channel: {channel.remote_pubkey}\nCapacity: {channel.capacity} satoshis"
                        ),
                        loop
                    )
                    previous_channels.add(channel.chan_id)
        
            time.sleep(60)  # Adjust as needed
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring channels: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Error monitoring channels: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring channels: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Unexpected error monitoring channels: {e}"
                ),
                loop
            )
        time.sleep(60)  # Check every 60 seconds

def monitor_forwarding_events(application, loop):
    stub = get_ln_stub()
    previous_forwardings = set()
    while True:
        try:
            response = stub.ForwardingHistory(ForwardingHistoryRequest())
            for event in response.forwarding_events:
                if event.chan_id_in not in previous_forwardings:
                    asyncio.run_coroutine_threadsafe(
                        application.bot.send_message(
                            chat_id=CHAT_ID,
                            text=f"🔄 Forwarding Event:\n"
                                 f"   - Channel In: {event.chan_id_in}\n"
                                 f"   - Channel Out: {event.chan_id_out}\n"
                                 f"   - Amount: {event.amt_in} satoshis\n"
                                 f"   - Fee: {event.fee} satoshis\n"
                                 f"   - Timestamp: {event.timestamp}"
                        ),
                        loop
                    )
                    previous_forwardings.add(event.chan_id_in)
        
            time.sleep(60)  # Adjust as needed
        except grpc.RpcError as e:
            logging.error(f"gRPC error while monitoring forwarding events: {e.details()}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Error monitoring forwarding events: {e.details()}"
                ),
                loop
            )
        except Exception as e:
            logging.error(f"Unexpected error while monitoring forwarding events: {e}")
            asyncio.run_coroutine_threadsafe(
                application.bot.send_message(
                    chat_id=CHAT_ID,
                    text=f"⚠️ Unexpected error monitoring forwarding events: {e}"
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
    Thread(target=monitor_lightning_transactions, args=(application, loop)).start()
    Thread(target=monitor_channels, args=(application, loop)).start()
    Thread(target=monitor_forwarding_events, args=(application, loop)).start()

    application.run_polling()

if __name__ == "__main__":
    main()
