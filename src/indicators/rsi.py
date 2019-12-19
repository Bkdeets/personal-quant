import logging
class RSI:
    def __init__(self, period, prices, ticker):
        self.period = period
        self.prices = prices
        self.ticker = ticker
        self.rsis = [0 for i in range(0, self.period)]
        self.avgsog = 0
        self.avgsol = 0
        self.calculate()

    def initRS(self):
        gains = []
        losses = []

        for i in range(1, self.period):
            change = float(self.prices[i]) - float(self.prices[i-1])

            if (change >= 0):
                gains.append(change)

            else:
                losses.append(-change)

        AvgSog = sum(gains) / self.period
        AvgSol = sum(losses) / self.period
        if AvgSol != 0:
            RS = AvgSog / AvgSol
        else:
            RS = 0

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
            change = float(self.prices[i]) - float(self.prices[i-1])
            if i == self.period:
                self.rsis.append(100 - (100 / (1 + RS)))
            elif i > self.period:
                self.updateRSI(change)
            else:
                continue