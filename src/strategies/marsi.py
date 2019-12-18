from src.indicators.sma import SMA
from src.indicators.rsi import RSI
from src.strategies.AStrategy import AStrategy
from ..wrappers import polygon as p
from ..utility.utility import Utility
import logging

class Marsi(AStrategy):

    def __init__(self, env, params):
        super().__init__(env, params)
        self.strategy_code = 'MAR'

    def getSmaIndication(self, current_price, current_sma, ticker):
        if current_price:
            positions = Utility().getPositionsByStrategy(self.strategy_code, self.API)
            holdings = {p.symbol: p for p in positions}
            holding_symbols = list(holdings.keys())
            indication = None

            isPriceGreater = current_price > current_sma
            isDistanceGreaterThanLevel = abs((current_price-current_sma)/current_sma) > self.params.get('sma').get('level') 
            
            if ticker in holding_symbols:
                position = holdings.get(ticker)
                if position.side == 'long':
                    if isPriceGreater and isDistanceGreaterThanLevel:
                        indication = 'exit'
                        return indication
                else:
                    if not isPriceGreater and isDistanceGreaterThanLevel:
                        indication = 'exit'
                        return indication
            else:
                if not isPriceGreater and isDistanceGreaterThanLevel:
                    indication = 'buy'
                    return indication
                elif isPriceGreater and isDistanceGreaterThanLevel:
                    indication = 'short'
                    return indication
            return indication
        return None

    def getRsiIndication(self, current_price, current_rsi, ticker):
        positions = Utility().getPositionsByStrategy(self.strategy_code, self.API)
        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        indication = None

        topLevel = self.params.get('rsi').get('topLevel')
        bottomLevel = self.params.get('rsi').get('bottomLevel')

        isLong = current_rsi < bottomLevel
        isShort = current_rsi > topLevel

        if ticker in holding_symbols:
            position = holdings.get(ticker)
            if position.side == 'long':
                if isShort:
                    indication = 'exit'
                    return indication
            else:
                if isLong:
                    indication = 'exit'
                    return indication
        else:
            if isLong:
                indication = 'buy'
                return indication
            elif isShort:
                indication = 'short'
                return indication
        return indication

    
    def getShares(self, price, position_size):
        account = self.API.get_account()
        value = account.cash + account.equity
        avail_cap = value * position_size

        shares = avail_cap//price

        if account.daytrading_buying_power >= shares*price:
            return shares
        else:
            return account.daytrading_buying_power//price

    
    def getIndicationOrder(self, smaIndication, rsiIndication, side, position_size, ticker, current_price):
        if smaIndication == 'exit' or rsiIndication == 'exit':
            if side == 'long':
                return {
                    'symbol': ticker,
                    'qty': Utility().getPosition(self.strategy_code, ticker, self.API).qty,
                    'side': 'sell'
                }
            elif side == 'short':
                return {
                    'symbol': ticker,
                    'qty': Utility().getPosition(self.strategy_code, ticker, self.API).qty,
                    'side': 'buy'
                }
        if smaIndication and rsiIndication:
            if smaIndication == 'buy' and rsiIndication == 'buy':
                shares = self.getShares(current_price, position_size)
                return {
                        'symbol': ticker,
                        'qty': shares,
                        'side': 'buy',
                        'stop': abs(current_price * (self.params.get('sl')-1))
                    }
            elif smaIndication == 'short' and rsiIndication == 'short':
                shares = self.getShares(current_price, position_size)
                return {
                        'symbol': ticker,
                        'qty': shares,
                        'side': 'sell',
                        'stop': current_price * (1+self.params.get('sl'))
                    }
        return None

    def get_orders(self, current_price=0, position_size=.05, prices_df=0):
        orders = []
        if not prices_df.empty:
            for ticker in self.params.get('assets'):
                if not self.env == 'backtest':
                    current_price = p.get_current_price(ticker)
                
                logging.info(f'{self.strategy_code}: Getting orders for {ticker}')

                self.sma = SMA(self.params.get('period'), prices_df.get(ticker).get('close'), ticker)
                self.rsi = RSI(self.params.get('period'), prices_df.get(ticker).get('close'), ticker)
                current_sma = self.sma.smas[-1]
                current_rsi = self.rsi.rsis[-1]
                self.params['sma']['level'] = self.sma.apds[-1][0] + self.sma.apds[-1][1]

                smaIndication = self.getSmaIndication(current_price, current_sma, ticker)
                rsiIndication = self.getRsiIndication(current_price, current_rsi, ticker)
                
                logging.info(f'{self.strategy_code}: SMA: {current_sma} Indication: {smaIndication}')
                logging.info(f'{self.strategy_code}: RSI: {current_rsi} Indication: {rsiIndication}')

                current_side = Utility().getCurrentSide(self.strategy_code, ticker, self.API)

                order = self.getIndicationOrder(
                    smaIndication, 
                    rsiIndication, 
                    current_side, 
                    position_size, 
                    ticker,
                    current_price
                )
                if order:
                    orders.append(order)
        return orders