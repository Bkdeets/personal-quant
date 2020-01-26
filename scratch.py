# from src.executor import Executor
# import pandas as pd
# from src.strategies.marsi import Marsi
# from src.indicators.rsi import RSI
# from src.indicators.sma import SMA
# marsi_params = {
#     'sma':{
#         'level': .005
#     },
#     'rsi':{
#         'topLevel': 65,
#         'bottomLevel': 35
#     },
#     'sl':.05,
#     'period':30,
#     'assets': ['AAPL'],
#     'needs_prices': True,
#     'timeframe': 'minute'
# }
# start = pd.Timestamp.now() - pd.Timedelta(days=2)
# e = Executor('paper',Marsi('paper',marsi_params))
# prices = e.get_prices(start).get('AAPL').get('close').fillna(method='ffill')
# list_prices = list(prices)
# sma = SMA(30,list_prices,'AAPL')
# print(sma.smas)
# rsi = RSI(30,list_prices,'AAPL')
# print(rsi.rsis)

# print(1/0)