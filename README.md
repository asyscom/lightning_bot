

# Lightning Node Telegram Bot

This Telegram bot integrates with a Lightning Network Daemon (LND) node to provide real-time updates and information about the node's status, channels, transactions, and more. It is built using Python and the `python-telegram-bot` library along with gRPC for communication with the LND node.

## Features

- **Node Info**: Retrieve and display detailed information about the LND node, including its alias, version, block height, on-chain balance, Lightning balance, and system metrics (CPU usage, memory, disk space, and CPU temperature).
- **Channel Info**: Get information about the Lightning channels, including their capacities and balances.
- **Recent Transactions**: Fetch and display recent on-chain transactions and Lightning invoices.
- **Routing Transactions**: Display recent Lightning routing transactions.
- **Monitoring**: Continuously monitor and notify about:
  - New on-chain transactions.
  - Settled Lightning invoices.
  - Changes in the status of Lightning channels.

## Setup

### Prerequisites

- Python 3.8+
- Telegram Bot API Token
- LND Node with gRPC enabled
- Properly configured TLS certificates and macaroon files

### Installation

1. **Clone the Repository:**

    ```bash
    git clone https://github.com/yourusername/your-repo.git
    cd your-repo
    ```

2. **Install Dependencies:**

    Ensure you have `python-telegram-bot` and `grpcio` installed. You can install them using pip:

    ```bash
    pip install python-telegram-bot grpcio
    ```

3. **Configuration:**

    Edit the script to set the appropriate values for:
    
    - `TELEGRAM_TOKEN`: Your Telegram bot API token.
    - `CHAT_ID`: The chat ID where the bot will send messages.
    - `LND_DIR`: Path to the directory containing your LND data (`tls.cert` and `admin.macaroon`).

    ```python
    TELEGRAM_TOKEN = 'your-telegram-bot-token'
    CHAT_ID = 'your-chat-id'
    LND_DIR = '/path/to/your/lnd/data/'
    ```

4. **Run the Bot:**

    Execute the script to start the bot:

    ```bash
    python lightning_bot.py
    ```

## Commands

- `/start`: Start the bot and display the main menu.
- `/menu`: Display the main menu.

### Inline Keyboard Options

- **⚡ Node Info**: Displays detailed information about the node.
- **📊 Channel Info**: Shows information about Lightning channels.
- **🔄 Recent Transactions**: Lists recent on-chain transactions and Lightning invoices.
- **🔄 Routing Transactions**: Provides details on recent routing transactions.

## Monitoring

The bot also continuously monitors:

- **On-chain Transactions**: Alerts you to new on-chain transactions.
- **Lightning Invoices**: Notifies you when a Lightning invoice is settled.
- **Lightning Channels**: Sends alerts if a monitored Lightning channel goes offline.

## Troubleshooting

- Ensure the paths to the TLS certificate and macaroon file are correct.
- Verify that the `lncli` command-line tool works with your LND setup.
- Check that the Telegram bot token and chat ID are correctly set.

## Logging

The bot logs errors and important information to the console. Ensure that the logging level is set to `INFO` or higher to capture all relevant events.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contributing

Feel free to open issues or submit pull requests if you have suggestions for improvements or fixes.

---

Feel free to customize the README as needed for your specific use case and repository.

How to Donate

Bitcoin (BTC): bc1q282pz0tkx0a8c96jgg5ms7mmjaxvd5gvww0rdk

Lightning Network: asyscom@sats.mobi

Thank you for your support!
