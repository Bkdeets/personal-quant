class RSI:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.rsis = []
        self.avgsog = 0
        self.avgsol = 0
        self.calculate()

    def sumList(self,list):
        sum = 0
        for i in list:
            sum += i
        return sum

    def initRS(self):
        gains = []
        losses = []

        for i in range(1, self.period):
            change = float(self.prices.iloc[i,:].close) - float(self.prices.iloc[i-1,:].close)

            if (change >= 0):
                gains.append(change)

            else:
                losses.append(-change)

        AvgSog = self.sumList(gains) / self.period
        AvgSol = self.sumList(losses) / self.period
        RS = AvgSog / AvgSol

        sip = [RS, AvgSog, AvgSol, gains, losses]

        return sip


    def updateRSI(self, priceChange):
        if priceChange > 0:
            self.avgsog = ((self.avgsog * (self.period-1)) + priceChange) / self.period
            self.avgsol = ((self.avgsol * (self.period-1)) - 0) / self.period
        elif priceChange < 0:
            self.avgsol = ((self.avgsol * (self.period-1)) - priceChange) / self.period
            self.avgsog = ((self.avgsog * (self.period-1)) - 0) / self.period
        if self.avgsol == 0:
            RS = 100
        else:
            RS = self.avgsog / self.avgsol
        self.rsis.append(100 - (100 / (1 + RS)))


    def calculate(self):
        nah = self.initRS()
        RS = nah[0]
        self.avgsog = nah[1]
        self.avgsol = nah[2]

        for i in range(2, len(self.prices)):
            change = float(self.prices.iloc[i,:].close) - float(self.prices.iloc[i - 1,:].close)
            if i == self.period:
                self.rsis.append(100 - (100 / (1 + RS)))
            elif i > self.period:
                self.updateRSI(change)
            else:
                self.rsis.append(0)




