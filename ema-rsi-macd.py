import numpy as np
import pandas as pd
import talib
import ccxt

# Set up the exchange and trading pair
exchange = ccxt.binance({
    'apiKey': 'your_api_key',
    'secret': 'your_secret',
})

symbol = 'BTC/USDT'

# Set up the technical indicators
ema_period = 20
rsi_period = 14
macd_fast_period = 12
macd_slow_period = 26
macd_signal_period = 9

# Set up the initial values
balance = exchange.fetch_balance()
usdt_balance = balance['USDT']['free']
btc_balance = balance['BTC']['free']
last_buy_price = None
last_sell_price = None

# Define the trading function
def trade():
    global usdt_balance, btc_balance, last_buy_price, last_sell_price
    
    # Get the historical data
    ohlcv = exchange.fetch_ohlcv(symbol, '1d')
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Calculate the technical indicators
    df['ema'] = talib.EMA(df['close'], timeperiod=ema_period)
    df['rsi'] = talib.RSI(df['close'], timeperiod=rsi_period)
    macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=macd_fast_period, slowperiod=macd_slow_period, signalperiod=macd_signal_period)
    df['macd'] = macd
    df['macdsignal'] = macdsignal
    df['macdhist'] = macdhist
    
    # Get the current prices
    ticker = exchange.fetch_ticker(symbol)
    current_price = ticker['last']
    
    # Check the trading conditions
    buy_condition = df['macd'][-1] > df['macdsignal'][-1] and df['rsi'][-1] < 30 and current_price > df['ema'][-1]
    sell_condition = df['macd'][-1] < df['macdsignal'][-1] and df['rsi'][-1] > 70 and current_price < df['ema'][-1]
    
    # Execute the trades
    if buy_condition:
        if usdt_balance > 10:
            # Buy BTC with USDT
            amount = (usdt_balance * 0.95) / current_price
            exchange.create_market_buy_order(symbol, amount)
            usdt_balance = 0
            btc_balance += amount
            last_buy_price = current_price
            print(f"Bought {amount:.8f} BTC at {current_price:.2f} USDT/BTC")
    elif sell_condition:
        if btc_balance > 0.0001:
            # Sell BTC for USDT
            amount = btc_balance * 0.95
            exchange.create_market_sell_order(symbol, amount)
            btc_balance = 0
            usdt_balance += amount
            last_sell_price = current_price
            print(f"Sold {amount:.8f} BTC at {current_price:.2f} USDT/BTC")
    
    # Print the balances and last trade prices