import statistics as st
import logging
class SMA:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.smas = [0 for x in range(0, period-1)]
        self.apds = [(0,0) for x in range(0, period-1)]
        self.distances = [0 for x in range(0, period-1)]
        self.calculate()

    def calculate(self):
        for i in range(self.period-1, len(self.prices)):
            print(i)
            sma = st.mean([price for price in self.prices[i - (self.period-1):i+1]])
            price = self.prices[i]
            self.distances.append(abs((price-sma)/sma))
            apd = st.mean([distance for distance in self.distances[i-(self.period-1):i+1]])
            stdev = st.stdev([distance for distance in self.distances[i-(self.period-1):i+1]])
            self.apds.append((apd,stdev))
            self.smas.append(sma)
