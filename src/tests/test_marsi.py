from ..strategies.marsi import Marsi
import datetime
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
        return True
    def get_activities(self, activity_types='default'):
        return True
class TestMarsi:
    def beforeEach(self, params={'default':True}):
        self.m = Marsi('test', params)
        self.m.API = MockApi()
    
    def test_initializes(self):
        self.beforeEach()
        assert self.m.params.get('default')