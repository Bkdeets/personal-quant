from src.strategies.AStrategy import AStrategy
from ..wrappers import polygon as p
from ..utility.utility import Utility
import logging

class LongShort(AStrategy):

    def __init__(self, env, params):
        super().__init__(env, params)
        self.strategy_code = 'LS'

    def getShares(self, price, position_size):
        account = self.API.get_account()
        value = float(account.cash) + float(account.equity)
        avail_cap = value * position_size

        shares = avail_cap//price

        if float(account.buying_power) >= shares*price:
            return shares
        else:
            return float(account.buying_power)//price

    def getChanges(self, prices):
        changes = []
        for i in range(0,len(prices)-2):
            changes.append(prices[i] - prices[i+1])
        return changes

    def isLong(self, prices):
        changes = self.getChanges(prices)
        pos = len([c for c in changes if c > 0])
        neg = len(changes) - pos
        if pos > neg:
            return True
        return False
    
    def isShort(self, prices):
        changes = self.getChanges(prices)
        pos = len([c for c in changes if c > 0])
        neg = len(changes) - pos
        if pos < neg:
            return True
        return False

    def _get_orders(self, prices, period, side, ticker, current_price):
        orders = []
        isLong = self.isLong(prices)
        isShort = self.isShort(prices)
        changes = self.getChanges(prices)
        pos = len([c for c in changes if c > 0])
        neg = len(changes) - pos
        if isLong:
            direction = 'buy'
        elif isShort:
            direction = 'sell'
        else:
            return []

        shares = self.getShares(current_price, .1)

        orders.append({
            'symbol': ticker,
            'qty': shares,
            'side': direction
        })

        if side:
            if side == 'sell' and not isLong:
                orders.append({
                    'symbol': ticker,
                    'qty': Utility().getPosition(self.strategy_code, ticker, self.API).qty,
                    'side': 'buy'
                })
            if side == 'buy' and isLong:
                orders.append({
                    'symbol': ticker,
                    'qty': Utility().getPosition(self.strategy_code, ticker, self.API).qty,
                    'side': 'buy'
                })
        return orders

    def get_orders(self, current_price=0, position_size=.1, prices_df=0):
        orders = []
        period = self.params.get('period')
        if not prices_df.empty:
            for ticker in self.params.get('assets'):
                if not self.env == 'backtest':
                    current_price = p.get_current_price(ticker)
                
                logging.info(f'{self.strategy_code}: Getting orders for {ticker}')

                closes = prices_df.get(ticker).get('close').dropna()
                list_of_prices = list(closes)

                current_side = Utility().getCurrentSide(self.strategy_code, ticker, self.API)
                    
                _orders = self._get_orders(list_of_prices, period, current_side, ticker, current_price)

                if _orders:
                    for order in _orders:
                        orders.append(order)
        return orders