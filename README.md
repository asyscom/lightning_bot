Got it! Here's the updated README with the correct repository URL:

---

# Lightning Node Telegram Bot

## Overview

The Lightning Node Telegram Bot is a Python-based bot that interfaces with your Lightning Network Daemon (LND) to provide real-time updates and management capabilities through Telegram. It allows you to monitor various aspects of your Lightning node, including channel status, on-chain transactions, forwarding transactions, and Lightning invoices.

## Features

- **Channel Monitoring**: Alerts you when a channel goes offline or comes back online.
- **On-Chain Transaction Monitoring**: Notifies you of new on-chain transactions.
- **Lightning Invoice Monitoring**: Provides notifications for received Lightning payments.
- **Forwarding Transaction Monitoring**: Keeps track of forwarding transactions and notifies you of new events.

## Installation

### Prerequisites

- **Python 3.11 or higher**
- **gRPC Python library** (`grpcio` and `grpcio-tools`)
- **Python Telegram Bot library** (`python-telegram-bot`)
- **psutil** (for system information)

### Setup

1. **Clone the Repository**

   ```bash
   git clone https://github.com/asyscom/lightning_bot.git
   cd lightning_bot
   ```

2. **Install Dependencies**

   Create a virtual environment and install the required packages:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. **Configuration**

   - Update the `TELEGRAM_TOKEN` and `CHAT_ID` with your Telegram bot token and chat ID.
   - Configure the path to your LND directory, TLS certificate, and macaroon in the `LND_DIR`, `CERT_PATH`, and `MACAROON_PATH` variables respectively.

4. **Run the Bot**

   Start the bot with:

   ```bash
   python bot_telegram.py
   ```

## Usage

- **/start**: Initiates interaction with the bot and shows the main menu.
- **/menu**: Displays a menu with options to view node information, channel details, recent transactions, and forwarding transactions.

### Menu Options

- **⚡ Node Info**: Displays information about the Lightning node, including version, block height, balances, and system metrics.
- **📊 Channel Info**: Lists details of all channels including capacity and balances.
- **🔄 Recent Transactions**: Shows recent on-chain transactions and Lightning invoices.
- **🔄 Forwarding Transactions**: Lists recent forwarding transactions with detailed information.

## Notes

- The bot continuously monitors your node and sends notifications for new forwarding transactions, changes in channel status, on-chain transactions, and Lightning payments.
- Ensure your bot has appropriate permissions and your Telegram bot token and chat ID are correctly configured.

## Troubleshooting

- **If the bot is not responding**: Ensure the LND gRPC interface is accessible and the paths to the certificate and macaroon are correct.
- **Notification issues**: Check the Telegram bot token and chat ID configurations.

---


How to Donate

Bitcoin (BTC): bc1q282pz0tkx0a8c96jgg5ms7mmjaxvd5gvww0rdk

Lightning Network: asyscom@sats.mobi

Thank you for your support!
