from datetime import datetime
import pandas as pd
import os
import alpaca_trade_api as tradeapi
from ..utility.utility import Utility
from ..indicators.sma import SMA
from ..indicators.rsi import RSI
import matplotlib.pyplot as plt
import pprint

class MarsiBacktest():
    API = tradeapi.REST(
        key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
        secret_key=os.getenv('ALPACA_PAPER_KEY'),
        base_url='https://paper-api.alpaca.markets')
    
    def __init__(self, params, symbol, start, timeframe, balance):
        self.params = params
        self.symbol = symbol
        self.data = Utility().get_prices(start, timeframe, [symbol], self.API, limit=1000)
        pprint.pprint(self.data)

        period = params.get('period')
        self.sma = SMA(period, self.data.get(symbol).get('close'), symbol)
        self.rsi = RSI(period, self.data.get(symbol).get('close'), symbol)

        self.balance = balance
        self.position = {
            'inPosition' : False,
            'side' : None,
            'entryPrice' : None
        }
        self.balances = self.itertest()

    def getSmaIndiction(self, sma, price):
        indication = None
        if sma > 0:
            isPriceGreater = price > sma
            isDistanceGreaterThanLevel = abs((price-sma)/sma) > self.params.get('sma').get('level') 

            if self.position.get('inPosition'):
                if self.position.get('side') == 'long':
                    if isPriceGreater and isDistanceGreaterThanLevel:
                        #print('sma exit')
                        indication = 'exit'
                        return indication
                else:
                    if not isPriceGreater and isDistanceGreaterThanLevel:
                        #print('sma exit')
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


    def getRsiIndiction(self, rsi):
        indication = None
        if rsi > 0:
            topLevel = self.params.get('rsi').get('topLevel')
            bottomLevel = self.params.get('rsi').get('bottomLevel')
            isLong = rsi < bottomLevel
            isShort = rsi > topLevel
            if self.position.get('inPosition'):
                if self.position.get('side') == 'long':
                    if isShort:
                        # print('rsi exit')
                        indication = 'exit'
                        return indication
                else:
                    if isLong:
                        # print('rsi exit')
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
    

    def checkStop(self, price):
        if self.position.get('inPosition'):
            if self.position.get('side') == 'long':
                if self.position.get('stop') >= price:
                    
                    # print('stopped')
                    # print(self.position)
                    return True
            else:
                if self.position.get('stop') <= price:
                    # print('stopped')
                    # print(self.position)
                    return True
        return False


    def getIndication(self, index):
        sma = self.sma.smas[index]
        self.params['sma']['level'] = self.sma.apds[index][0] + self.sma.apds[index][1]
        rsi = self.rsi.rsis[index]
        price = self.data.iloc[index,:][-2]
        if self.checkStop(price):
            return {'exit' : True}
    
        smaIndication = self.getSmaIndiction(sma, price)
        rsiIndication = self.getRsiIndiction(rsi)
        # if smaIndication and rsiIndication:
            # print(str(index) + " sma: " + str(smaIndication) + "  rsi: " + str(rsiIndication))
        if smaIndication == 'exit' or rsiIndication == 'exit':
            return {
                'exit': True
                }
        if smaIndication and rsiIndication:
            if smaIndication == 'buy' and rsiIndication == 'buy':
                return {
                        'side': 'long',
                        'stop': price * (self.params.get('sl')-1)
                    }
            elif smaIndication == 'short' and rsiIndication == 'short':
                return {
                        'side': 'short',
                        'stop': price * (1+self.params.get('sl'))
                    }
        return None

    
    def itertest(self):
        balances = [self.balance]
        actions = []
        close_prices = []
        for i in range(self.params.get('period')+1, len(self.data)):
            indication = self.getIndication(i)
            current_price = self.data.iloc[i,:][-2]
            close_prices.append(current_price)
            if indication:
                if indication.get('exit'):
                    if self.position.get('side') == 'short':
                        change = (self.position.get('entryPrice')-current_price)/self.position.get('entryPrice')
                        actions.append('so')
                    else:
                        change = (current_price-self.position.get('entryPrice'))/self.position.get('entryPrice')
                        actions.append('lo')
                    # print(current_price)
                    # print(self.position.get('entryPrice'))
                    # print(change)
                    # print('-----')
                    self.balance = self.balance * (1+change)
                    balances.append(self.balance)
                    self.position = {'inPosition' : False}    
                    continue
                else:
                    if indication.get('side') == 'short':
                        actions.append('si')
                    else:
                        actions.append('li')
                    self.position = {
                        'inPosition' : True,
                        'side' : indication.get('side'),
                        'entryPrice' : current_price,
                        'stop' : indication.get('stop')
                    }
            else:
                actions.append(None)

        fig, axs = plt.subplots(2, 1)

        axs[0].plot(close_prices)
        axs[0].plot(self.sma.smas[self.params.get('period')+1:])
        axs[1].plot(self.rsi.rsis[self.params.get('period')+1:])

        for i in range(0,len(actions)):
            action = actions[i]
            if action == 'si':
                axs[0].plot(i, close_prices[i], "b+")
            elif action == 'so':
                axs[0].plot(i, close_prices[i], "r+")
            elif action == 'li':
                axs[0].plot(i, close_prices[i], "gx")
            elif action == 'lo':
                axs[0].plot(i, close_prices[i], "rx")

        plt.show()

        return balances
