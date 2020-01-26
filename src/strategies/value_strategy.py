import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import os
from datetime import datetime, date, timedelta
from ..strategies.AStrategy import AStrategy
from ..utility.utility import Utility
from ..wrappers import polygon as p
from ..utility import value_funcs as v

class ValueStrategy(AStrategy):
    API = {}
    
    def __init__(self, env, params):
        super().__init__(env, params)
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        self.NY = 'America/New_York'
        self.strategy_code = 'VLU'
        self.params = params
    
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
        activities = self.API.get_activities(activity_types='FILL')
        for position in positions:
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
                'stop': current_price * self.params.get('sl')-1
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
        positions = Utility().getPositionsByStrategy(self.strategy_code, self.API)
        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        expired = self.checkForExpired(positions)
        to_buy_orders = self.processBuys(position_size, holding_symbols)
        to_sell_orders = self.processSells(expired)
        orders = [o for o in to_buy_orders]
        for o in to_sell_orders:
            orders.append(o)
        return orders