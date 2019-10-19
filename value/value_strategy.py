import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
import os
from . import value
from . import PolygonWrapper as pw 


class ValueStrategy():
    API = tradeapi.REST(
        key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
        secret_key=os.getenv('ALPACA_PAPER_KEY'),
        base_url='https://paper-api.alpaca.markets')

    def __init__(self, params):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)

        self.NY = 'America/New_York'
        self.id = 1

        self.api = None
        self.params = params

    def get_orders(self, position_size=.02):

        to_buy = value.get_check_for_buys(self.params.get('assets'))
        account = self.API.get_account()

        # now get the current positions and see what to buy,
        # what to sell to transition to today's desired portfolio.
        positions = self.API.list_positions()
        self.logger.info(positions)

        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        to_buy = [order[0] for order in to_buy if order[0] not in holding_symbols]
        to_sell = []

        for position in positions:
            current_price = pw.get_current_price(position['symbol'])
            entry_price = position['avg_entry_price']
            if (current_price - entry_price)/entry_price > self.params.get('tp'):
                to_sell.append(position)


        buying_power = self.API.get_account().buying_power
        
        orders = []
        for position in to_sell:
            orders.append({
                'symbol': position['symbol'],
                'qty': position['qty'],
                'side': 'sell'
            })
        for symbol in to_buy:
                current_price = pw.get_current_price(symbol)
                shares = (float(buying_power) * float(position_size)) // current_price
                if shares == 0.0:
                    continue
                orders.append({
                    'symbol': symbol,
                    'qty': shares,
                    'side': 'buy',
                    'stop': current_price * self.params.get('sl')
                })
                self.logger.info(f'order(buy): {symbol} for {shares}')
        return orders