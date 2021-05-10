import json, config
from flask import Flask, request, jsonify, render_template
from binance.client import Client
from binance.enums import *

app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET)

# general functions
def order(side, quantity, symbol, stopPrice, order_type=ORDER_TYPE_MARKET):
    
    try:
        if stopPrice:
            order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity, stopPrice=stopPrice)
        else:
            order = client.futures_create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return order

def percentage_change(start_value, end_value):
    return float(abs(start_value - end_value) / start_value)

@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)
    
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    symbol = "BTCUSDT"
    side = data['strategy']['order_action'].upper()
    quantity = data['strategy']['order_contracts']
    order_response = order(side, quantity, symbol )

    if order_response:
        return {
            "code": "success",
            "message": "order executed"
        }
    else:
        print("order failed")

        return {
            "code": "error",
            "message": "order failed"
        }

@app.route('/breakout', methods=['POST'])
def breakout():

    data = json.loads(request.data)

    # check
    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return {
            "code": "error",
            "message": "Nice try, invalid passphrase"
        }

    # parse tradingview webhook data
    take_profit_target = 2
    symbol_future = data['symbol'].find('PERP')
    symbol = data['symbol'][:symbol_future]
    entry_price = data['open']
    pv_high = data['pv_high']
    pv_low  = data['pv_low']
    risk = float(data['risk'])
    side_main = "BUY" if data['go_long'] == 1 else "SELL"
    side_cross = "SELL" if data['go_long'] == 1 else "BUY"
    stop_loss_perc = percentage_change(entry_price, pv_low if side_main == "BUY" else pv_high)

    # set leverage to maximum allowe
    if client:
        
        leverage = client.futures_change_leverage(symbol=symbol, leverage='30')
        print('Initializing leverage for', symbol, ':', leverage['leverage'], 'x')
 
    # set parameters to create binance order
    if stop_loss_perc:

        quantity = round((risk / stop_loss_perc) / entry_price)
        stop_loss = pv_low if side_main == "BUY" else pv_high

        take_profit = ((stop_loss_perc * take_profit_target)) * entry_price
        take_profit = take_profit + entry_price if side_main == "BUY" else abs(take_profit - entry_price)
        
        print(f'placing MARKET-{side_main} order for symbol {symbol} quantity {quantity} estimatedEntry {entry_price}')
        
        
        order_main = order(side_main, quantity, symbol, 0, order_type='MARKET')


        

        if order_main:
                
            print(f'placing STOP_MARKET-{side_cross} order for symbol {symbol} quantity {quantity} stopPrice {stop_loss} ')
            order_stop = order(side_cross, quantity, symbol, stop_loss, order_type='STOP_MARKET')

            print(f'placing TAKE_PROFIT_MARKET-{side_cross} order for symbol {symbol} quantity {quantity} stopPrice {take_profit} ')
            order_take = order(side_cross, quantity, symbol, take_profit, order_type='TAKE_PROFIT_MARKET')

        else:
        
            print("Error placing main MARKET order-{side_main} order for symbol {symbol} quantity {quantity} ")

        if order_take:
            return {
                "code": "success",
                "message": "order executed"
            }
        else:
            print("order failed")

    return {
        "code": "error",
        "message": "order failed"
    }