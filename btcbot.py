import websocket, numpy as np, json
import inspect
from talib import abstract


cc = 'btcusd'
interval = '1m'
socket = f'wss://stream.binance.com:9443/ws/{cc}/t@kline_{interval}'

amount = 1000
core_trade_amount = amount*0.9
core_quantity = 0
trade_amount = amount*0.1
core_to_trade = True
transaction_cost = 0.005
min_trade_amt = 30

portfolio = 0
investment, real_time_portfolio_value, closes, highs, lows, opens, volumes = [], [], [], [], [], [], []
money_end = amount
candles = [opens, highs, lows, closes, volumes]

def buy(quantity, price):
    global portfolio, money_end
    allocated_money = quantity * price
    money_end = money_end - allocated_money - transaction_cost * allocated_money
    portfolio += quantity
    if investment == []:
        investment.append(allocated_money)
    else:
        investment.append(allocated_money)
        investment[-1] += investment[-2]

def sell(quantity, price):
    global portfolio, money_end
    allocated_money = quantity * price
    money_end = money_end + allocated_money - transaction_cost * allocated_money
    portfolio -= quantity
    investment.append(-allocated_money)
    investment[-1] += investment[-2]

f = abstract
dir1 = dir(f)
public_method_names = [method for method in dir1 if method.startswith('CDL')]

def on_message(ws, message):
    global portfolio, investment, closes, highs, lows, money_end, core_to_trade, core_quantity, real_time_portfolio_value
    json_message = json.loads(message)
    cs = json_message['k']
    candle_closed, close, high, low, open, volume = cs['x'], cs['c'], cs['h'], cs['l'],cs['o'], cs['v']
    candle = [open, high, low, close, volume]
    if candle_closed:
        for i in candles:
            i.append(float(candle[candles.index(i)]))
        print(f'Closes: {closes}')
        inputs = {
    'open': np.array(opens),
    'high': np.array(highs),
    'low': np.array(lows),
    'close': np.array(closes),
    'volume': np.array(volumes)
}
        if core_to_trade:
            buy(core_trade_amount, closes[-1])
            print(f'Core Investment: We bought ${core_trade_amount} worth of Bitcoin', '\n')
            core_quantity += core_trade_amount / closes[-1]
            core_to_trade = False

        indicators = []
        for method in public_method_names:
            indicator = getattr(f, method)(inputs)
            indicators.append(indicator[-1])
        av_indicator = np.mean(indicators)
        print(av_indicator)

        if av_indicator >= 10:
            amt = trade_amount
        elif av_indicator <= -10:
            amt = trade_amount
        else:
            amt = av_indicator*10

        port_value = portfolio*closes[-1] - core_quantity*closes[-1]
        trade_amt = amt - port_value
        RT_portfolio_value = money_end + portfolio*closes[-1]
        real_time_portfolio_value.append(float(RT_portfolio_value))
        print(f'Average of all indicators is "{av_indicator}" and recommended exposure is "${amt}"')
        print(f'Real-Time Portfolio Value: {RT_portfolio_value}','\n')
        print(f'Invested amount: ${portfolio*closes[-1]}')

        if trade_amt > min_trade_amt:
            buy(trade_amt, closes[-1])
            print(f'We bought ${trade_amt} worth of Bitcoin','\n','\n')
        elif trade_amt < min_trade_amt:
            sell(-trade_amt, closes[-1])
            print(f'We sold ${-trade_amt} worth of Bitcoin','\n','\n')

ws = websocket.WebSocketApp(socket, on_message=on_message)

ws.run_forever()
