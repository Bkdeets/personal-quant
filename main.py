from macross import MACrossPaper
import executor

intentional error to cause execution to stop (oofO


macross_params = {
    'period': 20,
    'timeframe': '1Min',
    'assets': [
        'AAPL',
        'TSLA',
        'SIRI',
        'F',
        'BAC',
        'RRR',
        'GOOG',
        'SNAP',
        'GE',
        'SPY',
        'QQQ',
        'ACB'
    ]
}

strategies = [
    MACrossPaper(macross_params)
]

for strategy in strategies:
    executor.beginTrading(strategy)
