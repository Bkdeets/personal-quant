import pandas as pd
from ...wrappers import polygon as p

class MockAPI:

    def __init__(self, strategyInstance):
        self.strat = strategyInstance
        self.currentDate = strategyInstance.params.startDate
        self.account = MockAccount()
        self.initDateTimeList()
        self.initDataDF()
        self.fillPriceData()
        self.clock = MockClock()
        self.dateIndex = 0
        self.positions = []
    
    def initDateTimeList():
        self.datetimes = []
        end = self.strat.params.endDateTime
        increment = self.getIncrement()
        currentDT = self.strat.params.startDateTime
        while currentTime < end:
            currentDT = currentDT + increment
            self.datetimes.append(currentDT)
        self.datetimes.append(end)

    def getIncrement():
        timeframe = self.strat.params.timeframe
        if timeframe == 'minute':
            return datetime.timedelta(minutes=1)
        if timeframe == 'day'
            return datetime.timedelta(days=1)
        self.period = timeframe
        return datetime.timedelta(days=1)
    
    def initDataDF():
        data = [[]]
        df = pd.DataFrame(data, columns=self.strat.params.assets, index=self.datetimes)
        self.data = df

    def fillPriceData():
        start = self.strat.params.startDateTime.date()
        end = self.strat.params.endDateTime.date()
        for asset in self.strat.params.assets:
            aggs = p.get_aggregates(asset, start, end, period=self.period)
            for i in range(0, len(aggs.results)-1):
                self.data.loc(self.datetimes[i], asset) = aggs.results[i].c

    def getCurrentPrice(symbol):
        return self.data.loc(self.datetimes[self.dateIndex], symbol)

    def shouldTrade():
        return self.dateIndex < (len(self.datetimes) -1)

    # Mocked API functions
    def list_positions(self):
        return self.positions

    def get_clock():
        self.clock.reset(self.datetimes[self.dateIndex[i]])
        return self.clock
    
    def submit_order(
        self,
        symbol='AAPL',
        qty=0,
        side='buy',
        type='market',
        time_in_force='day',
        client_order_id=1234
    ):
        currentPrice = getCurrentPrice(symbol)
        

    


        




            symbol=ticker,
            qty=units,
            side='sell',
            type=order_type,
            time_in_force='day',
            client_order_id=self.strategy_instance.strategy_code+str(uuid.uuid1()))

    
    # TODO: list_orders
    # TODO: list_positions
    # TODO: get_barset
    # TODO: get_clock
    # TODO: get_account