import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import os
from datetime import datetime, date, timedelta

from ..wrappers import polygon as p
from ..utility import value_funcs as v

class ValueStrategy():
    API = {}
    
    def __init__(self, env, params):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        self.NY = 'America/New_York'
        self.id = 1
        self.params = params
        if env == 'test':
            self.API = {}
        elif env == 'paper':
            self.API = tradeapi.REST(
                key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
                secret_key=os.getenv('ALPACA_PAPER_KEY'),
                base_url='https://paper-api.alpaca.markets')
        elif env == 'live':
            self.API = tradeapi.REST(
                key_id=os.getenv('APCA_API_KEY_ID'),
                secret_key=os.getenv('APCA_API_SECRET_KEY'),
                base_url=os.getenv('APCA_API_BASE_URL'))

    
    def checkForSellsTP(self, positions):
        to_sell = []
        for position in positions:
                try:
                    current_price = p.get_current_price(position['symbol'])
                except:
                    continue
                entry_price = position['avg_entry_price']
                if (current_price - entry_price)/entry_price > self.params.get('tp'):
                    to_sell.append(position)
        return to_sell


    def checkForExpired(self, positions):
        to_sell = []
        currentDate = date.today()
        for position in positions:
            activities = self.API.get_activities(activity_types='FILL')
            for event in activities:
                if event.symbol == position.symbol:
                    entryDate = datetime.strptime(str(event.transaction_time).split(' ')[0],'%Y-%m-%d').date()
                    if (currentDate - timedelta(days=90)) >= entryDate:
                        to_sell.append(position)
        return to_sell
    
    def processBuys(self, position_size, holding_symbols):
        account = self.API.get_account()
        orders = []
        to_buy = v.get_check_for_buys(.4, self.params.get('assets'))
        if to_buy:
            to_buy = [order[0] for order in to_buy if order[0] not in holding_symbols]
        else:
            return []
        for symbol in to_buy:
            try:
                current_price = p.get_current_price(symbol)
            except:
                continue
            shares = (float(account.buying_power) * position_size) // current_price
            if shares == 0.0:
                continue
            orders.append({
                'symbol': symbol,
                'qty': shares,
                'side': 'buy',
                'stop': current_price * self.params.get('sl')
            })
        return orders
    
    def processSells(self, expired):
        orders = []
        for pos in expired:
            orders.append({
                'symbol': pos['symbol'],
                'qty': pos['qty'],
                'side': 'sell'
            })
        return orders

    def get_orders(self, position_size=.05):
        positions = self.API.list_positions()
        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        expired = self.checkForExpired(positions)
        to_buy_orders = self.processBuys(position_size, holding_symbols)
        to_sell_orders = self.processSells(expired)
        orders = [o for o in to_buy_orders]
        for o in to_sell_orders:
            orders.append(o)
        return orders

# class Position():
#     def __init__(self, symbol):
#         self.symbol = symbol
#
# sp5 = ['AAPL']
# value_params = {
#     'timeframe': 'day',
#     'assets': sp5,
#     'needs_prices': False,
#     'tp': .50,
#     'sl': .50
# }
# strat = ValueStrategy(value_params)
# print(strat.checkForExpired([Position('SEE')]))