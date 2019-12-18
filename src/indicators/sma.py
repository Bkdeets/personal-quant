import statistics as st
import logging
class SMA:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices

        logging.info(f'MAR: SMA: {prices}')
        logging.info(f'MAR: SMA: {period}')
        self.ticker = ticker
        self.smas = [0 for x in range(0, period+1)]
        self.apds = [0 for x in range(0, period+1)]
        self.distances = [0 for x in range(0, period+1)]
        self.calculate()

    def calculate(self):
        for i in range(0,len(self.prices)):
            if i >= self.period:
                sma = st.mean([price for price in self.prices[i - self.period:i]])
                price = self.prices[i]
                self.distances.append(abs((price-sma)/sma))
                apd = st.mean([distance for distance in self.distances[i-self.period:i]])
                stdev = st.stdev([distance for distance in self.distances[i-self.period:i]])
                self.apds.append((apd,stdev))
                self.smas.append(sma)


