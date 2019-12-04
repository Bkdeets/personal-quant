from ..strategies.value_strategy import ValueStrategy
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
class TestValueStrategy:
    def beforeEach(self, params={'default':True}):
        self.v = ValueStrategy('test', params)
        self.v.API = MockApi()
    
    def test_initializes(self):
        self.beforeEach()
        assert self.v.params.get('default')
    
    def test_checkForSellsTP_sell(self):
        params = {
            'tp': .001
        }
        self.beforeEach(params=params)
        positions = [{
            'symbol': 'AAPL',
            'avg_entry_price': 1
        }]
        to_sell = self.v.checkForSellsTP(positions)
        assert len(to_sell) == 1
    
    def test_checkForSellsTP_no_sell(self):
        params = {
            'tp': 10000
        }
        self.beforeEach(params=params)
        positions = [{
            'symbol': 'AAPL',
            'avg_entry_price': 10000
        }]
        to_sell = self.v.checkForSellsTP(positions)
        assert len(to_sell) == 0
    
    def test_checkForExpired_expired(self):
        self.beforeEach()
        def mock_get_activities_old(activity_types='FILL'):
            obj = MockObj(
                symbol='AAPL',
                transaction_time='2010-1-1 blahblah')
            return [obj]
        mock_position = MockObj(symbol='AAPL')
        api = MockApi()
        api.get_activities = mock_get_activities_old
        self.v.API = api
        expired = self.v.checkForExpired([mock_position])
        assert len(expired) == 1
    
    def test_checkForExpired_not_expired(self):
        self.beforeEach()
        def mock_get_activities_new(activity_types='FILL'):
            today = datetime.date.today()
            d1 = today.strftime('%Y-%m-%d')
            obj = MockObj(
                symbol='AAPL',
                transaction_time=d1+' blahblah')
            return [obj]
        mock_position = MockObj(symbol='AAPL')
        api = MockApi()
        api.get_activities = mock_get_activities_new
        self.v.API = api
        expired = self.v.checkForExpired([mock_position])
        assert len(expired) == 0
    
    # Cant test fully until I mock polygon wrapper
    def test_processBuys(self):
        params = {
            'assets': ['AAPL']
        }
        self.beforeEach(params=params)
        result = self.v.processBuys(.10, ['AAPL'])
        assert len(result) == 0

    def test_processSells(self):
        self.beforeEach()
        expired = [{
            'symbol': 'AAPL',
            'qty': 1000
        }]
        orders = self.v.processSells(expired)
        assert len(orders) == 1
        assert orders[0].get('side') == 'sell'
        assert orders[0].get('qty') == 1000
        assert orders[0].get('symbol') == 'AAPL'
    
    def test_get_orders(self):
        params = {
            'assets': ['AAPL']
        }
        self.beforeEach(params=params)
        def list_positions():
            return [MockObj(symbol='AAPL', id='2')]
        def mock_get_activities_new(activity_types='FILL'):
            today = datetime.date.today()
            d1 = today.strftime('%Y-%m-%d')
            obj = MockObj(
                symbol='AAPL',
                transaction_time=d1+' blahblah'
                id='3')
            return [obj]
        api = MockApi()
        api.list_positions = list_positions
        api.get_activities = mock_get_activities_new
        self.v.API = api
        result = self.v.get_orders()
        assert len(result) == 0


        

    

    
    

