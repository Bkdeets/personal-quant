from macross import MACrossPaper
import executor

macross_params = {
    'period': 20,
    'timeframe': '1Min',
    'assets': ['AAPL', 'TSLA', 'SIRI', 'F', 'BAC', 'RRR', 'SPY']
}

strategies = [
    MACrossPaper(macross_params)
]

print('y tho')
for strategy in strategies:
    executor.beginTrading(strategy)