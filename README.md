
# Telegram Bot for Lightning Network Monitoring

## Overview

This Telegram bot provides real-time monitoring and interaction with the Lightning Network (LN) and Bitcoin blockchain. It offers functionalities such as node information, channel details, recent transactions, forwarding events, and Bitcoin price updates.

## Features

- **Node Info**: Displays detailed node information including CPU usage, memory, disk space, and CPU temperature.
- **Channel Info**: Provides information about each Lightning channel, including capacity and balances.
- **Recent Transactions**: Lists recent on-chain and Lightning transactions with timestamps.
- **Forwarding Transactions**: Shows recent forwarding events with detailed information.
- **Bitcoin Info**: Displays Bitcoin price and network fee estimates in USD and EUR.

## Requirements

- Python 3.8+
- `grpcio` and `grpcio-tools`
- `python-telegram-bot`
- `psutil`
- `requests`

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/yourrepository.git
   cd yourrepository
   ```

2. **Install Dependencies:**

   Ensure you have `pip` installed. Then install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

   Alternatively, you can manually install the dependencies:

   ```bash
   pip install grpcio grpcio-tools python-telegram-bot psutil requests
   ```

3. **Configure Environment Variables:**

   Set up the following environment variables:

   - `TELEGRAM_TOKEN`: Your Telegram Bot API token.
   - `CHAT_ID`: The chat ID where the bot sends notifications.
   - `LND_DIR`: Path to the LND directory.

   You can set these in your `.env` file or export them directly in your terminal session:

   ```bash
   export TELEGRAM_TOKEN="your_telegram_bot_token"
   export CHAT_ID="your_chat_id"
   export LND_DIR="/path/to/lnd"
   ```

4. **Setup gRPC:**

   Ensure your gRPC setup for the Lightning Network Daemon (LND) is correctly configured. Place the `tls.cert` and `admin.macaroon` files in the specified `LND_DIR`.

## Usage

1. **Run the Bot:**

   Start the bot with the following command:

   ```bash
   python bot.py
   ```

   Ensure that you have set up the monitoring threads to handle different aspects like transactions, invoices, channels, and forwarding events.

2. **Interact with the Bot:**

   - **/start**: Displays the main menu with options to view node info, channel info, recent transactions, forwarding transactions, and Bitcoin info.
   - **/menu**: Shows the main menu again.

   Use the buttons provided in the Telegram chat to interact with the bot and get the relevant information.

## Monitoring Functions

- **On-Chain Transactions**: Monitors and notifies about new on-chain transactions.
- **Lightning Invoices**: Tracks and notifies about new settled Lightning invoices.
- **Channels**: Monitors channel statuses and notifies about online/offline changes.
- **Forwarding Events**: Monitors and notifies about new forwarding events.

## Error Handling

The bot includes error handling for:

- gRPC errors
- API request failures
- Unexpected exceptions

Logs are generated to help diagnose issues. Review the logs for more detailed error information.

## Contributing

Contributions are welcome! Please submit a pull request or open an issue to report bugs or suggest features.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For questions or support, please contact:

- **Author:** Your DavideBTC
- **Email:** davrago@proton.me

## Support the Project

If you found this guide helpful and would like to support the project, consider making a donation. Your contributions help maintain and improve this resource.

### Donate via Bitcoin
You can send Bitcoin directly to the following address:

**`bc1qy0l39zl7spspzhsuv96c8axnvksypfh8ehvx3e`**

### Donate via Lightning Network
For faster and lower-fee donations, you can use the Lightning Network:

**asyscom@sats.mobi**

Thank you for your support!
