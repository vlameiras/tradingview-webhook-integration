import logging
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from binance.client import Client
from binance.exceptions import BinanceAPIException
from binance.enums import *
import time
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Initialize the Binance Client
API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_API_SECRET")
TESTNET = os.getenv("BINANCE_TESTNET", "True").lower() in ["true", "1"]

FIX_USDT_AMOUNT = float(os.getenv("FIX_USDT_AMOUNT", "250"))  # Default is 250
LEVERAGE = int(os.getenv("LEVERAGE", "1"))  # Default leverage is 1

client = Client(API_KEY, API_SECRET, testnet=TESTNET)

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Item(BaseModel):
    ticker: str
    side: str
    entry: str
    tp1: str
    tp2: str
    tp3: str
    tp4: str
    winrate: str
    beTargetTrigger: str
    stop: str

app = FastAPI()

def set_leverage(client, symbol, leverage):
    try:
        client.futures_change_leverage(symbol=symbol, leverage=leverage)
        logging.info(f"Leverage set for {symbol} to {leverage}")
    except BinanceAPIException as e:
        logging.error(f"Error setting leverage for {symbol}: {e.message}")
        # Raise HTTPException, so FastAPI can generate a proper error response.
        raise HTTPException(status_code=400, detail=f"Error setting leverage: {e.message}")

def get_avg_price(client, symbol):
    avg_price_res = client.futures_ticker(symbol=symbol)
    return float(avg_price_res['lastPrice'])

def get_quantity(order_amount_usdt, avg_price):
    return order_amount_usdt / avg_price

def get_symbol_info(client, symbol):
    exchange_info = client.futures_exchange_info()
    return [s for s in exchange_info['symbols'] if s['symbol'] == symbol][0]

def get_precision(filters, filter_type):
    filter_data = [f for f in filters if f['filterType'] == filter_type][0]
    return float(filter_data['tickSize' if filter_type == 'PRICE_FILTER' else 'stepSize'])

def round_quantity(quantity, step_size):
    return round(quantity - (quantity % step_size), 8)

def create_order(client, params, quantity):
    try:
        order = client.futures_create_order(
            symbol=params['symbol'],
            side=params['side'],
            type=ORDER_TYPE_MARKET,
            quantity=quantity)
        return order
    except BinanceAPIException as e:
        logging.error(f"Error creating order: {e.message}")
        return None

def wait_for_order_to_fill(client, symbol, order_id):
    # Wait for the order to be filled
    while True:
        order_status = client.futures_get_order(
            symbol=symbol,
            orderId=order_id
        )
        if order_status['status'] == 'FILLED':
            return order_status
        elif order_status['status'] in ['CANCELED', 'EXPIRED']:
            raise Exception(f"Order was {order_status['status']}")
        time.sleep(0.1)  # 

def place_orders(client, params, take_profit_price, stop_loss_price):
    # Check if there are any open orders for the symbol
    open_orders = client.futures_get_open_orders(symbol=params['symbol'])
    if open_orders:
        logging.warning("There are already open orders for this symbol.")
        return None, None

    try:
        take_profit_order = client.futures_create_order(
            symbol=params['symbol'],
            side=SIDE_SELL if params['side'] == SIDE_BUY else SIDE_BUY,
            type=FUTURE_ORDER_TYPE_TAKE_PROFIT,
            quantity=params['quantity'],
            price=str(take_profit_price),
            stopPrice=str(take_profit_price)  # Trigger when it reaches the stop_loss_price
        )
        stop_loss_order = client.futures_create_order(
            symbol=params['symbol'],
            side=SIDE_SELL if params['side'] == SIDE_BUY else SIDE_BUY,
            type=FUTURE_ORDER_TYPE_STOP,
            quantity=params['quantity'],
            price=str(stop_loss_price),
            stopPrice=str(stop_loss_price)  # Trigger when it reaches the stop_loss_price
        )
        return take_profit_order['orderId'], stop_loss_order['orderId']
    except BinanceAPIException as e:
        logging.error(f"Error creating SL or TP order: {e.message}")
        logging.info("Canceling the original order...")
        try:
            client.futures_cancel_order(symbol=params['symbol'], orderId=params['order_id'])
        except BinanceAPIException as e:
            logging.error(f"Error canceling the original order: {e.message}")
            return None, None

@app.post("/webhook")
async def tradingview_webhook(item: Item):
    symbol_name, contract_type = item.ticker.split('.')
    params = {
        'symbol': symbol_name,
        'side': SIDE_BUY if item.side == "LONG" else SIDE_SELL,
        'type': ORDER_TYPE_MARKET,
        'order_price': float(item.entry),
        'take_profit_price': float(item.tp1),
        'stop_loss_price': float(item.stop),
        'leverage': LEVERAGE,  # Using ENV variable
        'fixed_usdt_amount': FIX_USDT_AMOUNT  # Using ENV variable
    }
    
    try:
        set_leverage(client, params['symbol'], params['leverage'])
        # Other functions called with exception handling
        symbol_info = get_symbol_info(client, params['symbol'])
        filters = symbol_info['filters']
        step_size = get_precision(filters, 'LOT_SIZE')
        quantity = get_quantity(params['fixed_usdt_amount'], get_avg_price(client, params['symbol']))
        params['quantity'] = round_quantity(quantity, step_size)
        order = create_order(client, params, params['quantity'])

        if order is not None:
            order_status = wait_for_order_to_fill(client, params['symbol'], order['orderId'])
            params['order_id'] = order_status['orderId']
            params['avg_price'] = order_status['avgPrice']
            take_profit_order_id, stop_loss_order_id = place_orders(client, params, params['take_profit_price'], params['stop_loss_price'])
            
            if take_profit_order_id is None or stop_loss_order_id is None:
                raise HTTPException(status_code=400, detail="Error: Take profit or stop loss order could not be created")

            return {"message": "Webhook received"}
        else:
            raise HTTPException(status_code=400, detail="Error: Order could not be created")

    except Exception as e:
        logging.error(f"Error in tradingview_webhook: {e}")
        raise HTTPException(status_code=500, detail=f"Error in tradingview_webhook: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
