from src.mocks.mockObject import MockObj
from src.mocks.account import Account

class MockApi:
    def __init__(self, account=Account()):
        self.account = account

    def list_positions(self):
        return self.account.positions

    def get_activities(self, activity_types='FILL'):
        return self.account.activities

    def get_account(self):
        return self.account

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