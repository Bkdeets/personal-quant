import alpaca_trade_api as tradeapi
import pandas as pd
import time
import logging
from src.indicators.sma import SMA
from src.strategies.AStrategy import AStrategy


class MACross(AStrategy):

    def __init__(self, env, params):
        super().__init__()
        self.strategy_code = 'MAX'

    def sort_func(self, sma_obj):
        return sma_obj.sma[-1]

    def rank(self, smas):
        return sorted(smas, key=self.sort_func)

    def checkToSell(self, sma, price):
        if sma > price:
            return True
        return False

    def checkToBuy(self, smas):
        toBuy = []
        for sma in smas:
            if sma.sma[-1] < sma.prices.iloc[-1,:].close:
                toBuy.append(sma)
        return toBuy


    def rankSMAS(prices_df):
        smas = []
        symbols = set()
        for col in prices_df.columns:
            symbols.add(col[0])

        c = 0
        for symbol in symbols:
            sma = SMA(self.params.get('period'), prices_df[symbol].dropna(), symbol)
            c += 1
            smas.append(sma)
        ranked = self.rank(smas)
        return ranked[::-1]
    
    def checkForSells(self):
        to_sell = [sma.ticker for sma in smas if sma.sma[-1] > sma.prices.iloc[-1,:].close and sma.ticker in holding_symbols]

        return


    def get_orders(self, prices_df=[], position_size=.05):

        ranked = self.rankSMAS(prices_df)

        to_buy = []
        account = self.API.get_account()

        # now get the current positions and see what to buy,
        # what to sell to transition to today's desired portfolio.
        positions = self.API.list_positions()
        self.logger.info(positions)

        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())

        to_sell = self.checkForSells(holdings)

        if holdings:

        ranked = self.checkToBuy(ranked[:max_positions])
        to_buy = [sma.ticker for sma in ranked]
        to_buy = to_buy[:len(to_sell)-1]

        orders = []


        # if a stock is in the portfolio, and not in the desired
        # portfolio, sell it
        for symbol in to_sell:
            shares = holdings[symbol].qty
            orders.append({
                'symbol': symbol,
                'qty': shares,
                'side': 'sell',
            })
            self.logger.info(f'order(sell): {symbol} for {shares}')

        # likewise, if the portfoio is missing stocks from the
        # desired portfolio, buy them. We sent a limit for the total
        # position size so that we don't end up holding too many positions.
        max_to_buy = max_positions - (len(positions) - len(to_sell))

        buying_power = self.API.get_account().buying_power

        for symbol in to_buy:

                if max_to_buy <= 0:
                    break

                shares = (float(buying_power) * float(position_size)) // prices_df[symbol].close.values[-1]

                if shares == 0.0:
                    continue
                orders.append({
                    'symbol': symbol,
                    'qty': shares,
                    'side': 'buy',
                })
                self.logger.info(f'order(buy): {symbol} for {shares}')
                max_to_buy -= 1

        return orders