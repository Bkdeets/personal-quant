import statistics as st
class SMA:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.sma = []
        self.calculate()

    def calculate(self):
        for i in range(0,len(self.prices)):
            if i >= self.period:
                self.sma.append(
                    st.mean(
                        [p.close for p in self.prices.iloc[i-self.period:i,:]]
                    )
                )


