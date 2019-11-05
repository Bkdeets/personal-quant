import logging
import pandas as pd
import time
import alpaca_trade_api as tradeapi
import os

API = tradeapi.REST(
        key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
        secret_key=os.getenv('ALPACA_PAPER_KEY'),
        base_url='https://paper-api.alpaca.markets')


def buy(ticker, order_type, units, limit_price=None):
    return API.submit_order(
        symbol=ticker,
        qty=units,
        side='buy',
        type='market',
        time_in_force='day',
    )


def bulkBuy(buys, wait=30):
    for order in buys:
        try:
            logging.info(f'submit(buy): {order}')
            buy(
                order['symbol'],
                'market',
                order['qty'])
        except Exception as e:
            logging.error(e)
    count = wait
    while count > 0 and len(buys) > 0:
        pending = API.list_orders()
        if len(pending) == 0:
            logging.info(f'all buy orders done')
            break
        logging.info(f'{len(pending)} buy orders pending...')
        time.sleep(1)
        count -= 1


def sell(ticker, order_type, units, limit_price=None):
    return API.submit_order(
        symbol=ticker,
        qty=units,
        side='sell',
        type=order_type,
        time_in_force='day',
    )


def bulkSell(sells, wait=30):
    for order in sells:
        try:
            logging.info(f'submit(sell): {order}')
            sell(
                order['symbol'],
                'market',
                order['qty'])

        except Exception as e:
            logging.error(e)
    count = wait
    while count > 0 and len(sells) > 0:
        pending = API.list_orders()
        if len(pending) == 0:
            logging.info(f'all sell orders done')
            break
        logging.info(f'{len(pending)} sell orders pending...')
        time.sleep(1)
        count -= 1


def trade(orders, wait=30):
    '''This is where we actually submit the orders and wait for them to fill.
    Waiting is an important step since the orders aren't filled automatically,
    which means if your buys happen to come before your sells have filled,
    the buy orders will be bounced. In order to make the transition smooth,
    we sell first and wait for all the sell orders to fill before submitting
    our buy orders.
    '''

    # process the sell orders first
    sells = [o for o in orders if o['side'] == 'sell']
    bulkSell(sells)

    # process the buy orders next
    buys = [o for o in orders if o['side'] == 'buy']
    bulkBuy(buys)


def get_prices(symbols, timeframe, start, end=None, limit=50, tz='America/New_York'):
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


def beginTrading(strategy_instance):
    logging.info('start running')
    timeframe_map = {
        '1Min': 1,
        '5Min': 5,
        'day' : 30
    }

    sleep = timeframe_map.get(strategy_instance.params.get('timeframe'))

    while True:
        clock = API.get_clock()
        now = clock.timestamp
        if clock.is_open:
            tradeable_assets = strategy_instance.params.get('assets')

            if strategy_instance.params.get('needs_prices'):
                logging.info('Getting prices...')
                start = pd.Timestamp.now() - pd.Timedelta(days=2)
                prices_df = get_prices(
                    tradeable_assets,
                    timeframe=strategy_instance.params.get('timeframe'),
                    start=start)
                
                logging.info('Getting orders...')
                orders = strategy_instance.get_orders(prices_df)
            else:
                logging.info('Getting orders...')
                orders = strategy_instance.get_orders()

            

            logging.info(orders)
            trade(orders)
            logging.info(API.get_account())
            logging.info(f'done for {clock.timestamp}')

        time.sleep(60 * sleep)
