import statistics as st
class SMA:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.smas = [0 for x in range(0, period+1)]
        self.apds = [0 for x in range(0, period+1)]
        self.distances = [0 for x in range(0, period+1)]
        self.calculate()

    def calculate(self):
        for i in range(1,len(self.prices.index)):
            if i > self.period:
                sma = st.mean([row[-2] for index, row in self.prices.iloc[i - self.period:i, :].iterrows()])
                price = self.prices.iloc[i,:][-2]
                self.distances.append(abs((price-sma)/sma))
                apd = st.mean([distance for distance in self.distances[i-self.period:i]])
                stdev = st.stdev([distance for distance in self.distances[i-self.period:i]])
                self.apds.append((apd,stdev))
                self.smas.append(sma)


