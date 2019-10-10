import pandas as pd
import alpaca_trade_api as tradeapi

API = tradeapi.REST(
        key_id='-',
        secret_key='-',
        base_url='https://paper-api.alpaca.markets')

def getData(symbols, timeframe, start, end=None, limit=50, tz='America/New_York'):
    '''
    Gets prices for list of symbols and returns a pandas df

                                      AAPL                    ...     BAC
                                  open     high      low  ...     low   close volume
    time                                                  ...
    2019-06-21 11:50:00-04:00  200.020  200.070  199.720  ...  28.420  28.435   6170
    2019-06-21 11:55:00-04:00  199.850  199.980  199.810  ...  28.410  28.435   6169
    '''

    if not end:
        end = pd.Timestamp.now(tz=tz)

    # List of Bars
    def get_barset(symbols):
        return API.get_barset(
            symbols,
            timeframe,
            limit=limit,
            start=start,
            end=end)

    # The maximum number of symbols we can request at once is 200.
    barset = None
    i = 0
    while i <= len(symbols) - 1:
        if barset is None:
            barset = get_barset(symbols[i:i+200])
        else:
            barset.update(get_barset(symbols[i:i+200]))
        i += 200

    # Turns barset into a df
    return barset.df
