
import PolygonWrapper as pw
ticker = 'AAPL'
fundamentals = pw.get_fundamentals(ticker, limit=40) #Quarterly -- 10 years
prices = pw.get_historical_prices(period='day',candles=)
print(len(fundamentals['results']))
