from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import pandas as pd
import Wrapper
import numpy as np
from sklearn.metrics import confusion_matrix
import AlphaVantageWrapper as avw

def normalize(alist):
    norms = []
    mi = min(alist)
    ma = max(alist)
    for item in alist:
        norm = round((item - mi) / (ma - mi), 2)
        norms.append(norm)
    return norms

# Alpaca stuff
# start = pd.Timestamp.now() - pd.Timedelta(days=365)
# df = Wrapper.getData([ticker], interval, start)
# closes = [c for c in df[ticker]['close']]

def test():
    ticker = 'AAPL'
    interval = '1min'
    lookback = 20
    closes = avw.getIntraday(ticker, interval)
    predictors = []
    predictees = []
    for i in range(0, len(closes)):
        if i >= lookback and i+1 < len(closes):
            predictor = closes[i-(lookback-1):i+1]
            predictor = normalize(predictor)
            predictors.append(predictor)
            if closes[i+1] - closes[i] <= 0:
                predictees.append(0)
            else:
                predictees.append(1)

    X_train, X_test, y_train, y_test = train_test_split(predictors, predictees, test_size=0.2, random_state=69)
    model = MultinomialNB().fit(X_train, y_train)

    predicted = model.predict(X_test)

    print("Accuracy")
    print(np.mean(predicted == y_test))

    print("Confusion Matrix")
    print(confusion_matrix(y_test, predicted))
