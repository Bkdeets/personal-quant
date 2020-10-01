from ..wrappers import polygon as p

class DataUtility:
    def __init__(self, strategyInstance):
        self.strat = strategyInstance
        self.cachedPrices = [] #df

    def get_current_price(self, ticker):
        if self.cachedPrices:
            return self.cachedPrices.get(ticker)[0]
        
        if self.strat.env == 'live' or self.strat.env == 'paper':
            return p.get_current_price(ticker)
        
        