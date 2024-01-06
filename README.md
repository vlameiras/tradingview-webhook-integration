
# TradingView Webhook Integration

## Overview

[![BuyMeACoffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/vascolameiras)

This is a trading bot that receives signals via a webhook from TradingView and performs trades. Currently, it is designed to work with the [imba-lance-algo](https://www.tradingview.com/script/xW8hYdbL-imba-lance-algo/) indicator on TradingView and Binance Futures.

Please note that this project is a work in progress, so use it at your own risk. I take no responsibility for issues or money lost while using it. This is distributed for educational purposes only.

## Features

- Uses the FastAPI web framework
- Leverages the Binance API for trading
- Configurable to potentially support other exchanges in the future
- Logs all activities to a file for transparency and troubleshooting
- Can be configured via environment variables or a .env file
- Supports both local and Docker Compose setup

## Existing Limitations

- Currently, it only works with Binance.
- It can work with any markets (not just futures), but custom development is needed to support other markets.
- Tests should initially be made on the Binance Testnet (`BINANCE_TESTNET=True`). An account and API key should be created at [Binance Testnet](https://testnet.binancefuture.com/en/futures/). Refer to [this guide](https://www.binance.com/en/support/faq/how-to-test-my-functions-on-binance-testnet-ab78f9a1b8824cf0a106b4229c76496d) for more details.

## Setting Up the Indicator and Alert on TradingView

1. On TradingView, open the [imba-lance-algo](https://www.tradingview.com/script/xW8hYdbL-imba-lance-algo/) indicator.
2. Click on the "Source Code" tab and make a working copy.
3. In the Pine Script editor, paste the copied code and make a change on line 573 to include the symbol/ticker:

```pinescript
alert_message = "\n{\n" +  "    \"side\": \"" + str.tostring(trade.side) + "\",\n    \"entry\": \"" + str.tostring(trade.entry_price) + "\",\n    \"tp1\": \"" + str.tostring(trade.tp1_price) + "\",\n    \"tp2\": \"" + str.tostring(trade.tp2_price) + "\",\n    \"tp3\": \"" + str.tostring(trade.tp3_price) + "\",\n    \"tp4\": \"" + str.tostring(trade.tp4_price) + "\",\n    \"winrate\": \"" + str.tostring(RoundUp(profit_trades / trade_count * 100, 2)) + "%" + "\",\n    \"ticker\": \"" + syminfo.ticker + "\",\n    \"beTargetTrigger\": \"" + break_even_target + "\",\n    \"stop\": \"" + str.tostring(trade.sl_price) + "\"\n}\n"
```

4. Save the script to create a working copy of the indicator.
5. You then need to create an alert. Choose the condition that triggers the alert as the script you saved in step 4, and set it to trigger on the `alert()` function call. The alert should be open-ended and not have an expiration.

## Local Setup

### Prerequisites

Python 3.11+ is recommended for this project.

### Steps

1. Clone the repository.
2. Install the required packages by running `pip install -r requirements.txt` in the project directory.
3. Create an API key at Binance that supports Futures trading. For more information, follow the instructions in [Binance API Management](https://www.binance.com/en/my/settings/api-management).
4. Create a `.env` file in the project directory and add your Binance API key and secret, and other configurations. Here's an example:

```env
BINANCE_API_KEY=YourBinanceAPIKey
BINANCE_API_SECRET=YourBinanceAPISecret
BINANCE_TESTNET=True
FIX_USDT_AMOUNT=250
LEVERAGE=5
```

5. Run the application with the command `uvicorn app:app --host 0.0.0.0 --port 8000`.

## Docker Compose Setup

### Prerequisites

Docker and Docker Compose are required for this setup. Please refer to Docker's official documentation for installation instructions.

### Steps

1. Clone the repository.
2. Create a `.env` file in the project directory with the same content as described in the Local Setup section.
3. Build the Docker image with the command `docker build -t your_docker_image_name .`.
4. Run the Docker Compose setup with the command `docker-compose up`.

## Usage

After you've set up the bot, configure your TradingView alerts to send POST requests to `http://your_server_ip:8000/webhook` with the payload as per the `Item` model in `app.py`.

You can test the webhook using this example curl command (ensure you are using Testnet):

```bash
curl -X POST "http://localhost:8000/webhook" \
-H "accept: application/json" \
-H "Content-Type: application/json" \
-d "{
  \"symbol\": \"PEOPLEUSDT.P\",
  \"side\": \"LONG\",
  \"entry\": \"0.04182\",
  \"tp1\": \"0.04224\",
  \"tp2\": \"0.04266\",
  \"tp3\": \"0.04307\",
  \"tp4\": \"0.04349\",
  \"winrate\": \"43.43%\",
  \"ticker\": \"PEOPLEUSDT.P\",
  \"beTargetTrigger\": \"1\",
  \"stop\": \"0.04128\"
}"
```

## Custom Development Requests

I am open to custom development requests. If you have specific needs or improvements you'd like to see in this project, feel free to reach out. You can contact me via email at lameiras@duck.com or reach out to Vasco in the IMBA Telegram group [here](https://t.me/imba_p_chat).

Your feedback and suggestions are highly valuable and contribute to further improving and expanding the capabilities of this project.


## Donations

If you find this project helpful and would like to support my work, donations of any size are greatly appreciated. You can send any cryptocurrencies of your choice such as ERC-20 (e.g. ETH, USDC) or BEP-20 (e.g. BNB).

ERC-20/BEP-20: `0xA1D7252E3E27C10DACacb8e4a84A0306d8E3f052`

Bitcoin: `33L8xQy4Bnhw86upyMFvyKKfaFKxn3WCFB`

Alternatively, consider buying me a coffee on [BuyMeACoffee](https://www.buymeacoffee.com/vascolameiras). Your generosity and support contribute to the continued development and improvement of this project.

[![BuyMeACoffee](https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png)](https://www.buymeacoffee.com/vascolameiras)

Your generosity and support contribute to the continued development and improvement of this project. Thank you!
