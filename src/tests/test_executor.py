from src.executor import Executor
import pytest
import datetime
class MockObj(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
class MockApi:
    def submit_order(self, symbol='AAPL', qty=1000, side='buy', type='market', time_in_force='day', client_order_id='2'):
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
    def list_positions(self):
        return []

class MockStrategy:
    strategy_code = 'test'
    params = {
        'timeframe': 'minute'
    }
    def getOrders(self):
        return [True]

class TestExecutor:
    def before_each(self):
        self.e = Executor('test', MockStrategy())
        self.e.setApi(MockApi())
    
    def test_buy(self):
        self.before_each()
        assert self.e.buy('AAPL', 'buy', 1000)

    # Bulk buy works with happy path
    def test_bulk_buy_happy_path(self):
        self.before_each()
        buys = [{
            'symbol': 'AAPL',
            'qty': 1000
        }]
        self.e.bulkBuy(buys, wait=0)
        assert True
    
    # Bulk buy try/catch works buy allowing execution to continue
    def test_bulk_buy_failed_buy(self):
        self.before_each()
        self.e.buy = lambda a,b,c: 1/0
        buys = [{
            'symbol': 'AAPL',
            'qty': 1000
        }]
        self.e.bulkBuy(buys, wait=0)
        assert True

    # Test sell
    def test_sell(self):
        self.before_each()
        assert self.e.sell('AAPL', 'market', 1000)

    # Bulk sell works with happy path
    def test_bulk_sell_happy_path(self):
        self.before_each()
        sells = [{
            'symbol': 'AAPL',
            'qty': 1000
        }]
        self.e.bulkSell(sells, wait=0)
        assert True
    
    # Bulk sell try/catch works buy allowing execution to continue
    def test_bulk_sell_failed_sell(self):
        self.before_each()
        self.e.sell = lambda a,b,c: 1/0
        sells = [{
            'symbol': 'AAPL',
            'qty': 1000
        }]
        self.e.bulkSell(sells, wait=0)
        assert True
  
    def test_trade_buys(self):
        self.before_each()
        orders = [{
            'symbol': 'AAPL',
            'qty': 1000,
            'side': 'buy'
        }]
        self.e.trade(orders, wait=0)
        assert True

    def test_trade_sells(self):
        self.before_each()
        orders = [{
            'symbol': 'AAPL',
            'qty': 1000,
            'side': 'sell'
        }]
        self.e.trade(orders, wait=0)
        assert True

    def test_get_prices(self):
        self.before_each()
        prices = self.e.get_prices(['AAPL'], 'day', 100)
        assert prices == True   
