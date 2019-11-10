import logging
import pandas as pd
import time
import alpaca_trade_api as tradeapi
import os
import threading


class Executor:
    API = {}
    timeframe_map = {
        '1Min': 1,
        '5Min': 5,
        'day' : 30
    }

    def __init__(self, env):
        self.initApi(env)
    
    def getApi(self):
        return self.API
    
    def setApi(self, api):
        self.API = api
    
    def initApi(self, env):
        if env == 'test':
            self.API = {}
        elif env == 'paper':
            self.API = tradeapi.REST(
                key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
                secret_key=os.getenv('ALPACA_PAPER_KEY'),
                base_url='https://paper-api.alpaca.markets')
        elif env == 'live':
            self.API = tradeapi.REST(
                key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
                secret_key=os.getenv('ALPACA_PAPER_KEY'),
                base_url='https://paper-api.alpaca.markets')


    def buy(self, ticker, order_type, units, limit_price=None):
        return self.API.submit_order(
            symbol=ticker,
            qty=units,
            side='buy',
            type='market',
            time_in_force='day')

    def bulkBuy(self, buys, wait=30):
        for order in buys:
            try:
                logging.info(f'submit(buy): {order}')
                self.buy(
                    order['symbol'],
                    'market',
                    order['qty'])
            except Exception as e:
                logging.error(e)
        count = wait
        while count > 0 and len(buys) > 0:
            pending = self.API.list_orders()
            if len(pending) == 0:
                logging.info(f'all buy orders done')
                break
            logging.info(f'{len(pending)} buy orders pending...')
            time.sleep(1)
            count -= 1


    def sell(self, ticker, order_type, units, limit_price=None):
        return self.API.submit_order(
            symbol=ticker,
            qty=units,
            side='sell',
            type=order_type,
            time_in_force='day',)

    def bulkSell(self, sells, wait=30):
        for order in sells:
            try:
                logging.info(f'submit(sell): {order}')
                self.sell(
                    order['symbol'],
                    'market',
                    order['qty'])
            except Exception as e:
                logging.error(e)
        count = wait
        while count > 0 and len(sells) > 0:
            pending = self.API.list_orders()
            if len(pending) == 0:
                logging.info(f'all sell orders done')
                break
            logging.info(f'{len(pending)} sell orders pending...')
            time.sleep(1)
            count -= 1

    def trade(self, orders, wait=30):
        sells = [o for o in orders if o['side'] == 'sell']
        self.bulkSell(sells, wait=wait)

        buys = [o for o in orders if o['side'] == 'buy']
        self.bulkBuy(buys, wait=wait)

    def get_prices(self, symbols, timeframe, start, end=None, limit=50, tz='America/New_York'):
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

        # The maximum number of symbols we can request at once is 200.
        barset = None
        i = 0
        while i <= len(symbols) - 1:
            if barset is None:
                barset = self.API.get_barset(
                    symbols[i:i+200],
                    timeframe,
                    limit=limit,
                    start=start,
                    end=end)
            else:
                barset.update(
                    self.API.get_barset(
                        symbols[i:i+200],
                        timeframe,
                        limit=limit,
                        start=start,
                        end=end))
            i += 200

        # Turns barset into a df
        return barset.df

    def beginTrading(self, strategy_instance):
        logging.info('start running')
        sleep = self.timeframe_map.get(strategy_instance.params.get('timeframe'))

        while True:
            clock = self.API.get_clock()
            if clock.is_open:
                tradeable_assets = strategy_instance.params.get('assets')

                if strategy_instance.params.get('needs_prices'):
                    logging.info('Getting prices...')
                    start = pd.Timestamp.now() - pd.Timedelta(days=2)
                    prices_df = self.get_prices(
                        tradeable_assets,
                        timeframe=strategy_instance.params.get('timeframe'),
                        start=start)
                    
                    logging.info('Getting orders...')
                    orders = strategy_instance.get_orders(prices_df)
                else:
                    logging.info('Getting orders...')
                    orders = strategy_instance.get_orders()

                logging.info(orders)
                self.trade(orders)
                logging.info(self.API.get_account())
                logging.info(f'done for {clock.timestamp}')

            time.sleep(60 * sleep)