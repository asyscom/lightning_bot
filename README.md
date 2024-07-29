Telegram Lightning Network Bot
This project is a Telegram bot designed to interact with a Lightning Network node, providing an easy-to-use interface for monitoring and managing the node's status and activities. It is particularly useful for users running a Lightning node on a Raspberry Pi or other hardware, such as with the RaspiBlitz setup.

Features
Node Information: Get detailed information about your Lightning node, including alias and block height.
Wallet Balance: Check the total and confirmed balance of your wallet in satoshis.
Channel Information: View details about your active channels, including their capacity and local balance.
Pending Invoices: Display pending invoices with their respective amounts.
Recent Transactions: Review recent transactions processed by your node.
Closed Channels Notifications: Receive notifications when channels are closed.
Requirements
Python 3.9 or higher
Telegram API token: Required to interact with the Telegram bot.
GRPC for Python: Used for communication with the Lightning Network node.


Certainly! Here's a description in English that you can use for your GitHub repository:

Telegram Lightning Network Bot
This project is a Telegram bot designed to interact with a Lightning Network node, providing an easy-to-use interface for monitoring and managing the node's status and activities. It is particularly useful for users running a Lightning node on a Raspberry Pi or other hardware, such as with the RaspiBlitz setup.

Features
Node Information: Get detailed information about your Lightning node, including alias and block height.
Wallet Balance: Check the total and confirmed balance of your wallet in satoshis.
Channel Information: View details about your active channels, including their capacity and local balance.
Pending Invoices: Display pending invoices with their respective amounts.
Recent Transactions: Review recent transactions processed by your node.
Closed Channels Notifications: Receive notifications when channels are closed.
Requirements
Python 3.9 or higher
Telegram API token: Required to interact with the Telegram bot.
GRPC for Python: Used for communication with the Lightning Network node.
Installation
Clone the repository:

git clone https://github.com/yourusername/telegram-lightning-bot.git
Install dependencies:
pip install -r requirements.txt

Set up the configuration:

Update TELEGRAM_TOKEN with your bot's API token.
Ensure your Lightning node's gRPC interface is accessible and configure the paths to the tls.cert and admin.macaroon files.
Run the bot:

python lightning_bot.py
