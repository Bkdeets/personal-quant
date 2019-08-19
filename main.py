from macross import MACrossPaper
import executor

macross_params = {
    'period': 20,
    'timeframe': '1Min',
    'assets': ['AAPL', 'TSLA', 'SIRI', 'F', 'BAC', 'RRR', 'SPY']
}

macross_params2 = {
    'period': 25,
    'timeframe': '1Min',
    'assets': ['AAPL', 'TSLA', 'SIRI', 'F', 'BAC', 'RRR', 'SPY']
}

strategies = [
    MACrossPaper(macross_params),
    MACrossPaper(macross_params2)
]

for strategy in strategies:
    executor.beginTrading(strategy)
    executor.beginTrading(strategy)