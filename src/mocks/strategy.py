default_params = {
    'timeframe': 'minute',
    'assets': ['AAPL']
}
class MockStrategy:    
    def __init__(self, strategy_code='test', params=default_params):
        self.strategy_code = strategy_code
        self.params = params

    def getOrders(self):
        return [True]