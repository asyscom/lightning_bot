Certainly! Here's the README description translated into English:

---

# Telegram Lightning Node Monitor Bot

## Description

This Telegram bot is designed to monitor and manage a Lightning Network node, providing real-time updates and details about various aspects of the node. It uses the `python-telegram-bot` library for integration with Telegram and `grpc` for communication with the Lightning node.

### Key Features

1. **Node Info**:
   - Displays detailed information about the node, including:
     - Node alias
     - Software version
     - Bitcoin block height
     - On-chain balance (total and confirmed)
     - Lightning balance (sum of local channel balances)
     - Total number of channels
     - System information such as CPU usage, free memory, and free SSD disk space

2. **Channel Info**:
   - Shows a list of open Lightning channels with:
     - Channel name
     - Channel capacity
     - Local and remote balances

3. **Recent Transactions**:
   - Displays the latest 10 transactions, both on-chain and Lightning:
     - On-chain transactions: transaction hash and amount
     - Lightning invoices: memo and amount paid

4. **Notifications**:
   - **On-chain Transactions**: Alerts when a new on-chain transaction is detected.
   - **Lightning Invoices**: Alerts when a Lightning payment is received.
   - **Channels**: Alerts when a channel goes offline.
   - **Routing**: Notifies when the node routes a transaction.

### Requirements

- Python 3.7+
- `python-telegram-bot`
- `grpcio`
- `psutil`
- Certificate and macaroon files from LND for authentication

### Configuration

1. **Telegram Bot Token**: Insert the Telegram bot token into the code.
2. **LND Configuration**: Configure the paths for the certificate and macaroon files for LND.
3. **Chat ID**: Specify the Telegram chat ID for receiving notifications.

### Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/your-username/telegram-lightning-node-monitor-bot.git
   ```

2. Navigate to the project directory:
   ```bash
   cd telegram-lightning-node-monitor-bot
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the variables in the code (`TELEGRAM_TOKEN`, `CHAT_ID`, `CERT_PATH`, `MACAROON_PATH`).

5. Run the bot:
   ```bash
   python bot_telegram.py
   ```

### Usage Example

Once started, the bot will connect to Telegram and be ready to receive commands. Use the `/start` command to view the main menu and interact with the various available options.

### Contributing

If you would like to contribute to the project, please submit a pull request or open an issue to discuss new features or bugs.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

Feel free to adjust the information to better fit your project and specific setup.
How to Donate

Bitcoin (BTC): bc1q282pz0tkx0a8c96jgg5ms7mmjaxvd5gvww0rdk

Lightning Network: asyscom@sats.mobi

Thank you for your support!
