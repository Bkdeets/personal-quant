from ..strategies.marsi import Marsi
import datetime
import pandas as pd 

class MockObj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
class MockApi:
    def submit_order(self, symbol='AAPL', qty=1000, side='buy', type='market', time_in_force='day'):
        return [{'status':200}]
    def list_orders(self):
        return [{'status':200}]
    def get_barset(self, symbols, timeframe, limit=10, start=10, end=10):
        def update(x):
            return True
        barset = MockObj(df=True, update=update)
        barset.df = True
        return barset
    def get_clock(self):
        return True
    def get_account(self):
        return MockObj(
            cash=1000,
            equity=1000,
            buying_power=2000
        )
    def get_activities(self, activity_types='default'):
        return True
class TestMarsi:
    def beforeEach(self, params={'default':True}):
        self.m = Marsi('test', params)
        self.m.API = MockApi()
    
    def test_initializes(self):
        self.beforeEach()
        assert self.m.params.get('default')

    def test_getSmaIndication(self):
        self.beforeEach()
        self.m.params['sma'] = {'level': .01}
        current_price = 100
        current_sma = 120
        ticker = 'YEEEEETED'
        result = self.m.getSmaIndication(current_price, current_sma, ticker)
        assert result == 'short'
    
    def test_getRsiIndication(self):
        self.beforeEach()
        self.m.params['rsi'] = {'topLevel': 65, 'bottomLevel': 35}
        current_price = 100
        current_rsi = 70
        ticker = 'YEEEEETED'
        result = self.m.getRsiIndication(current_price, current_rsi, ticker)
        assert result == 'short'

    def test_getShares(self):
        self.beforeEach()
        price = 1000
        position_size = 1
        result = self.m.getShares(price, position_size)
        assert result == 2

    def test_getIndicationOrder(self):
        self.beforeEach()
        smaIndication = 'buy'
        rsiIndication = 'buy'
        side = 'long'
        position_size = 1
        ticker = 'YAHEEEEHEHEHEEET'
        current_price = 10
        result = self.m.getIndicationOrder(smaIndication, rsiIndication, side, position_size, ticker, current_price)
        assert result.get('ticker') == ticker
    
    # def test_get_orders(self):
    #     self.beforeEach()
    #     prices_df = {'BREEEET': [1,2,3,4]}
  
    #     # initialize list of lists 
    #     data = [['close', 10], ['close', 15], ['close', 14]] 
        
    #     # Create the pandas DataFrame 
    #     df = pd.DataFrame(data, columns = ['Name', 'Age'])

