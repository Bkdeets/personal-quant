import alpha_vantage
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt

API_KEY = '-'

def getIntraday(ticker, interval):
    ts = TimeSeries(key=API_KEY, output_format='pandas')
    data, meta_data = ts.get_intraday(symbol=ticker,interval=interval, outputsize='full')
    return data['4. close']