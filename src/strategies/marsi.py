from src.indicators.sma import SMA
from src.indicators.rsi import RSI
from src.strategies.AStrategy import AStrategy
from ..wrappers import polygon as p
from ..utility.utility import Utility

class Marsi(AStrategy):

    def __init__(self, env, params):
        super().__init__(env, params)
        self.strategy_code = 'MAR'

    def getSmaIndication(self, current_price, current_sma, ticker):
        positions = Utility().getPositionsByStrategy(self.strategy_code, self.API)
        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        indication = None

        isPriceGreater = current_price > current_sma
        isDistanceGreaterThanLevel = abs((current_price-current_sma)/current_sma) > self.params.get('sma').get('level') 
        
        if ticker in holding_symbols:
            position = holdings.get(ticker)
            if position.get('side') == 'long':
                if isPriceGreater and isDistanceGreaterThanLevel:
                    indication = 'exit'
                    return indication
            else:
                if not isPriceGreater and isDistanceGreaterThanLevel:
                    indication = 'exit'
                    return indication
        else:
            if isPriceGreater and isDistanceGreaterThanLevel:
                indication = 'buy'
                return indication
            elif not isPriceGreater and isDistanceGreaterThanLevel:
                indication = 'short'
                return indication
        return indication

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
            if position.get('side') == 'long':
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

        if account.buying_power >= shares*price:
            return shares
        else:
            return account.buying_power//price

    
    def getIndicationOrder(self, smaIndication, rsiIndication, side, position_size, ticker, current_price):
        if smaIndication == 'exit' or rsiIndication == 'exit' and side:
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
                        'stop': current_price * (self.params.get('sl')-1)
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
        

    def get_orders(self, position_size=.02, prices_df={}):
        orders = []
        if prices_df:
            for ticker in self.params.get('assets'):
                current_price = p.get_current_price(ticker)
                sma = SMA(self.params.get('period'), prices_df.get('ticker'), ticker)
                rsi = RSI(self.params.get('period'), prices_df.get('ticker'), ticker)
                current_sma = sma.smas[-1]

                self.params['sma']['level'] = sma.apds[-1][0] + sma.apds[-1][1]
                current_rsi = rsi.rsis[-1]

                smaIndication = self.getSmaIndication(current_price, current_sma, ticker)
                rsiIndication = self.getRsiIndication(current_price, current_rsi, ticker)
                current_side = Utility().getCurrentSide(self.strategy_code, ticker, self.API)

                order = self.getIndicationOrder(
                    smaIndication, 
                    rsiIndication, 
                    current_side, 
                    position_size, 
                    ticker,
                    current_price)
                if order:
                    orders.append(order)

        return orders