import backtrader as bt
import math 
class SuppprtResistanceIndicator(bt.Indicator):
    lines = ('indication',)
    params = (('lookback', 40),)

    def myround(self, x, base=5):
        return round(base * round(x/base, 2),2)

    def getPricePattern(self, data):
        pattern = []
        for i in range(0, len(data)):
            if i != 0:
                if data[i] >= data[i-1]:
                    pattern.append(1)
                else:
                    pattern.append(-1)
        return pattern

    def getBehavior(self, pattern):
        # p = peak
        # v = valley
        # nc = no change
        # r = rising_count
        # f = falling
        # s = strong
        # w = weak

        avg = abs(sum(pattern)//len(pattern))
        mid = len(pattern)//2
        beg = sum(pattern[0:mid])
        end = sum(pattern[mid:-1])
        if sum(pattern) == 0:
            if beg > end:
                return 'sp'
            elif end > beg:
                return 'sv'
            else:
                return 'nc'
        elif -avg >= sum(pattern) <= avg:
            if beg > end:
                return 'p'
            elif end > beg:
                return 'v'
            else:
                return 'nc'
        elif sum(pattern) < -avg:
            if beg > end:
                return 'sf'
            elif end > beg:
                return 'wf'
            else:
                return 'f'
        elif sum(pattern) > avg:
            if beg > end:
                return 'wr'
            elif end > beg:
                return 'sr'
            else:
                return 'r'         

    def processData(self):
        # processed = {
        #     price: {
        #         volume,
        #         count,
        #         behaviors
        #     }
        # }
        processed = {}
        t = self.data.get(size=self.params.lookback).tolist()
        for i in range(0, len(t)):
            if i >=2 and i <= len(t)-2:
                price = self.myround(t[i])
                thefuckingprices = [i for i in t]
                behavior = self.getBehavior(self.getPricePattern(thefuckingprices[i-2:i+2]))
                if not price in processed:
                    processed[price] = {}
                    processed[price]['count'] = 0
                    #processed[price].volume = 0
                    processed[price]['behaviors'] = []

                processed[price]['count'] += 1
                #processed[price].volume += volume
                processed[price]['behaviors'].append(behavior)
        return processed


    def getSignal(self, comp, candle):
        # p = peak
        # v = valley
        # nc = no change
        # r = rising_count
        # f = falling
        # s = strong
        # w = weak
        
        #avg_vol = comp.volume // comp.count
        score = 0
        #if candle.volume >= avg_vol-avg_vol//4:
        for behavior in comp['behaviors']:
            if behavior == 'sp' or behavior == 'sf':
                score -= 3
            elif behavior == 'sv' or behavior == 'sr':
                score += 3
            elif behavior == 'p' or behavior == 'f':
                score -= 2
            elif behavior == 'v' or behavior == 'r':
                score += 2
            elif behavior == 'wf':
                score -= 1
            elif behavior == 'wr':
                score += 1

        if score > 0:
            return 1
        else:
            return -1
                

    def next(self):
        self.data.get(size=self.params.lookback).tolist()
        processed = self.processData()
        candle = self.data.get(size=1)[0]
        price = self.myround(candle)
        print("rouneded price")
        print(price)

        comparative_price = processed.get(price)
        if comparative_price:
            self.lines.indication[0] = self.getSignal(comparative_price, candle)
        else:
            self.lines.indication[0] = 0




    




