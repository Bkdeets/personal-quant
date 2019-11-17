import statistics as st
class SMA:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.smas = []
        self.calculate()

    def calculate(self):
        for i in range(0,len(self.prices.index)):
            if i > self.period:
                self.smas.append(
                    st.mean(
                        [row.close for index, row in self.prices.iloc[i - self.period:i, :].iterrows()]
                    )
                )


