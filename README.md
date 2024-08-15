# Lightning Node Telegram Bot

## Description

This Telegram bot interacts with a Lightning Network (LND) node to provide detailed information and monitor various activities. It uses gRPC for communication with LND and the `python-telegram-bot` library for interaction with Telegram.

## Features

- Displays node information, including balances and channel status.
- Shows Lightning channel information.
- Retrieves and displays recent transactions (both on-chain and Lightning).
- Shows forwarding events and network fee information.
- Monitors real-time Lightning invoices, transactions, and channel status.

## Dependencies

- `grpcio` and `grpcio-tools` for gRPC communication.
- `python-telegram-bot` for interacting with the Telegram API.
- `psutil` for system resource monitoring.
- `requests` for external API calls.
- `protobuf` for managing `.proto` files.

## Installation

1. **Clone the Repository**

    ```bash
    git clone https://github.com/asyscom/lightning_bot.git
    cd lightning_bot
    ```

2. **Install Dependencies**

    Create a virtual environment (optional but recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

    Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1. **Environment Variables**

    Configure the following environment variables:

    - `TELEGRAM_TOKEN`: The Telegram bot API token.
    - `CHAT_ID`: The Telegram chat ID to send messages to.
    - `LND_DIR`: Directory of LND data. Ensure it contains the `tls.cert` and `admin.macaroon` files.

    You can create a `.env` file to manage these variables:

    ```env
    TELEGRAM_TOKEN=your_telegram_token
    CHAT_ID=your_chat_id
    LND_DIR=/opt/data/lnd/
    ```

2. **.proto Files**

    Ensure you have the necessary `.proto` files for your project. The files are included in the `lightning_pb2.py` and `lightning_pb2_grpc.py` directories, generated using the `protoc` compiler. If you don't have these files, generate them with the following steps:

    - Install `protoc`:
    
      ```bash
      sudo apt-get install protobuf-compiler
      ```

    - Compile the `.proto` files:

      ```bash
      protoc --python_out=. --grpc_python_out=. lightning.proto
      ```

## Running the Bot

Run the bot with the command:

```bash
python bot.py
```

## Commands

- `/start`: Starts the bot and shows the main menu.
- `/menu`: Shows the main menu.

The bot also handles the following inline keyboard callbacks:

- **⚡ Node Info**: Displays node information.
- **📊 Channel Info**: Displays channel information.
- **🔄 Recent Transactions**: Displays recent transactions.
- **🔄 Forwarding Transactions**: Displays forwarding events.
- **💸 Network Fees**: Displays network fee information.

## Monitoring

The bot runs the following monitoring threads to track real-time activities:

- **On-chain transactions monitoring**
- **Lightning invoices monitoring**
- **Lightning transactions monitoring**
- **Channel monitoring**
- **Forwarding events monitoring**

## Debugging and Logging

Logs are configured to record errors and other relevant information. Logs are output to the console and can be viewed for debugging purposes.

## Contributing

If you want to contribute to this project, feel free to submit a pull request. Make sure to test your changes and update the documentation as necessary.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

Feel free to adapt the details to your specific requirements and configurations. If you have any further questions or need additional clarification, don’t hesitate to ask!
