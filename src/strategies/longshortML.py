# Long short strategy. 
# Daily
# Exit first thing in the morning
# Enter after exiting yesterdays trade, using yesterdays close price

# Using simple linear regression first, then adding more 

# params = {
#     timeframe: day,
#     needs_prices: false,
#     lookback: int,
#     posSize: int,
#     rsi: {
#         period: int
#     }
# }

# 1. Run strategy @ 9am
# 2. Calc next trade (nt)
# 3. if nt.side == ct.side
#         do nothing
#     else
#         exit ct and enter nt (ie. flip the trade)
#             (...order would be double the size)


from src.strategies.AStrategy import AStrategy
from ..wrappers import polygon as p
import numpy as n
import pandas as pd
from sklearn import linear_model
from src.indicators.rsi import RSI
from ..utility.utility import Utility
import logging
import pprint

class LongShortML(AStrategy):

    def __init__(self, env, params):
        super().__init__(env, params)
        self.strategy_code = 'LSML'
        self.po_map = {
            'sell':'short',
            'short':'sell',
            'buy':'long',
            'long':'buy'
        }

    def getChanges(self, prices):
        changes = [0]
        for i in range(1,len(prices)):
            changes.append((prices[i] - prices[i-1])/prices[i-1])
        return changes
    
    def getRsis(self, prices):
        rsi = RSI(self.params.get('rsi').get('period'), prices, 'NA')
        return rsi.rsis

    def getShares(self, price, position_size):
        account = self.API.get_account()
        value = float(account.cash) + float(account.equity)
        avail_cap = value * position_size
        shares = avail_cap//price
        if float(account.buying_power) >= shares*price:
            return shares
        else:
            return float(account.buying_power)//price
    
    def getDirection(self, prices, changes, rsis, current_price, ticker):
        # TODO: Make sure values are lined up

        previousPrices = [0]
        for i in range(0,len(prices)-1):
            previousPrices.append(prices[i])

        data = {
            'prices': prices,
            'changes': changes,
            'previousPrices': previousPrices
        }

        df = pd.DataFrame(data)
        df.dropna()
        df = df[(df.T != 0).all()]

        predDf = df[['changes','previousPrices']]
        tgtDf = df['prices']

        X = predDf
        y = tgtDf

        lm = linear_model.LinearRegression()
        model = lm.fit(X,y)

        score = lm.score(X,y)

        logging.info(f'{self.strategy_code}: Linear Regression score for {ticker}: {score}')

        predictions = lm.predict(X)

        pred_price = predictions[-1]

        logging.info(f'{self.strategy_code}: Predicted: {pred_price} Current: {current_price}')

        if pred_price > current_price:
            return 'buy'
        return 'sell'


    def get_orders(self, current_price=0, position_size=.1, prices_df=0):
        orders = []
        lookback = self.params.get('period')
        if not self.env == 'backtest':
            start = pd.Timestamp.now() - pd.Timedelta(days=lookback)
            prices_df = Utility().get_prices(
                start, 
                self.params.get('timeframe'), 
                self.params.get('assets'),
                self.API,
                limit=lookback
            )
        if not prices_df.empty:
            for ticker in self.params.get('assets'):
                if not self.env == 'backtest':
                    current_price = p.get_current_price(ticker)
                
                logging.info(f'{self.strategy_code}: Getting orders for {ticker}')

                closes = prices_df.get(ticker).get('close').dropna()
                list_of_prices = list(closes)

                changes = self.getChanges(list_of_prices)
                rsis = self.getRsis(list_of_prices)

                side = self.getDirection(list_of_prices, changes, rsis, current_price, ticker)
                current_side = Utility().getCurrentSide(self.strategy_code, ticker, self.API)

                if not current_side:
                    orders.append({
                        'symbol': ticker,
                        'qty': self.getShares(current_price, self.params.get('posSize')),
                        'side': side
                    })
                elif current_side and side != self.po_map.get(current_side):
                    curr_qty = Utility().getPosition(self.strategy_code, ticker, self.API).qty
                    orders.append({
                        'symbol': ticker,
                        'qty': curr_qty,
                        'side': side
                    })
                    orders.append({
                        'symbol': ticker,
                        'qty': self.getShares(current_price, self.params.get('posSize')),
                        'side': side
                    })

        return orders


