# -*- coding: utf-8 -*-
"""
Created on Sun Mar  3 21:10:42 2024

@author: ThanhTung
"""

import MetaTrader5 as mt5
import pandas as pd
#import numpy as np
import time

# Kết nối với mT5
mt5.initialize()

# Define functions to calculate technical indicators
def calculate_rsi(data, window=14):
    delta = data['close'].diff(1)
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(data, short_window=12, long_window=26):
    short_ema = data['close'].ewm(span=short_window, adjust=False).mean()
    long_ema = data['close'].ewm(span=long_window, adjust=False).mean()
    macd = short_ema - long_ema
    signal_line = macd.ewm(span=9, adjust=False).mean()
    return macd, signal_line

def calculate_bollinger_bands(data, window=20):
    sma = data['close'].rolling(window=window).mean()
    rolling_std = data['close'].rolling(window=window).std()
    upper_band = sma + 2 * rolling_std
    lower_band = sma - 2 * rolling_std
    return upper_band, lower_band

def identify_candlestick_patterns(data):
    patterns = []
    for i in range(2, len(data)):
        if data['open'][i] < data['close'][i] and data['open'][i - 1] > data['close'][i - 1] and data['close'][i - 1] < data['open'][i] and data['low'][i] > data['open'][i - 1] and data['low'][i] > data['close'][i - 1]:
            patterns.append(('Bullish Engulfing', data.index[i]))
        elif data['open'][i] > data['close'][i] and data['open'][i - 1] < data['close'][i - 1] and data['close'][i - 1] > data['open'][i] and data['high'][i] < data['open'][i - 1] and data['high'][i] < data['close'][i - 1]:
            patterns.append(('Bearish Engulfing', data.index[i]))
    return patterns

# Define functions to place trades
def place_buy_order(symbol, volume, sl_price, tp_price):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_BUY,
        "price": mt5.symbol_info_tick(symbol).ask,
        "sl": sl_price,
        "tp": tp_price,
        "magic": 123456,
        "comment": "Buy Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    print("Buy order result:", result)

def place_sell_order(symbol, volume, sl_price, tp_price):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick(symbol).bid,
        "sl": sl_price,
        "tp": tp_price,
        "magic": 123456,
        "comment": "Sell Order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    print("Sell order result:", result)

# Main loop
while True:
    # Danh sách các cặp tiền tệ
    currency_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]

    # Lặp qua từng cặp tiền tệ và thực hiện giao dịch
    for pair in currency_pairs:
        # Lấy dữ liệu cho cặp tiền tệ trong khoảng thời gian H1
        currency_data = mt5.copy_rates_from_pos(pair, mt5.TIMEFRAME_H1, 0, 100)

        # Chuyển dữ liệu thành DataFrame
        currency_df = pd.DataFrame(currency_data)
        currency_df['time'] = pd.to_datetime(currency_df['time'], unit='s')

        # Calculate RSI
        rsi = calculate_rsi(currency_df)

        # Calculate MACD
        macd, signal_line = calculate_macd(currency_df)

        # Calculate Bollinger Bands
        upper_band, lower_band = calculate_bollinger_bands(currency_df)

        # Identify candlestick patterns
        candlestick_patterns = identify_candlestick_patterns(currency_df)

        # Generate buy and sell signals
        buy_signals = []
        sell_signals = []
        for pattern, date in candlestick_patterns:
            if rsi[date] < 30 and macd[date] > signal_line[date] and currency_df['close'][date] > lower_band[date]:
                buy_signals.append((pair, pattern, date))
            elif rsi[date] > 70 and macd[date] < signal_line[date] and currency_df['close'][date] < upper_band[date]:
                sell_signals.append((pair, pattern, date))

        print("Pair:", pair)
        print("Buy Signals:", buy_signals)
        print("Sell Signals:", sell_signals)

        # Đặt lệnh mua và bán với giá lời và lỗ hợp lý nhất
        for pair, pattern, date in buy_signals:
            sl_price = currency_df['low'][date] - (currency_df['high'][date] - currency_df['low'][date]) * 2
            tp_price = currency_df['close'][date] + (currency_df['high'][date] - currency_df['low'][date]) * 3
            place_buy_order(pair, 0.1, sl_price, tp_price)

        for pair, pattern, date in sell_signals:
            sl_price = currency_df['high'][date] + (currency_df['high'][date] - currency_df['low'][date]) * 2
            tp_price = currency_df['close'][date] - (currency_df['high'][date] - currency_df['low'][date]) * 3
            place_sell_order(pair, 0.1, sl_price, tp_price)

    # Ngủ trong 5 phút trước khi kiểm tra lại
    time.sleep(300)  # 300 giây = 5 phút

# Đóng kết nối
mt5.shutdown()
