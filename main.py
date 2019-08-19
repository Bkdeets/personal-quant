from macross import MACrossPaper
import executor
import os
from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "We're up and runnin"

port = int(os.environ.get("PORT", 5000))
app.run(host='0.0.0.0', port=port)

macross_params = {
    'period': 20,
    'timeframe': '1Min',
    'assets': ['AAPL', 'TSLA', 'SIRI', 'F', 'BAC', 'RRR', 'SPY']
}

strategies = [
    MACrossPaper(macross_params)
]

for strategy in strategies:
    executor.beginTrading(strategy)