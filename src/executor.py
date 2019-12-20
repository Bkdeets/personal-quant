import logging
import pandas as pd
import time
import alpaca_trade_api as tradeapi
import os
import threading
import uuid 

class Executor:
    API = {}
    timeframe_map = {
        'minute': 1,
        '1Min': 1,
        '5Min': 5,
        'day' : 30
    }

    def __init__(self, env, strategy_instance):
        self.strategy_instance = strategy_instance
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
                key_id=os.getenv('APCA_API_KEY_ID'),
                secret_key=os.getenv('APCA_API_SECRET_KEY'),
                base_url=os.getenv('APCA_API_BASE_URL'))


    def buy(self, ticker, order_type, units, limit_price=None):
        return self.API.submit_order(
            symbol=ticker,
            qty=units,
            side='buy',
            type='market',
            time_in_force='day',
            client_order_id=self.strategy_instance.strategy_code+str(uuid.uuid1()))

    def filterExistingPositions(self, orders, side):
        orders = []
        positions = self.API.list_positions()
        holdings = {p.symbol: p for p in positions}
        for order in orders:
            if holdings.get(order.symbol) and holdings.get(order.symbol).side != side:
                orders.append(order)
            elif not holdings.get(order.symbol):
                orders.append(order)
        return orders

    def bulkBuy(self, buys, wait=30):
        buys = self.filterExistingPositions(buys, 'buy')
        for order in buys:
            try:
                logging.info(f'{self.strategy_instance.strategy_code} : submit(buy): {order}')
                self.buy(
                    order['symbol'],
                    'market',
                    order['qty'])
            except Exception as e:
                logging.error(f'{self.strategy_instance.strategy_code} : {e}')
        count = wait
        while count > 0 and len(buys) > 0:
            pending = self.API.list_orders()
            if len(pending) == 0:
                logging.info(f'{self.strategy_instance.strategy_code} : all buy orders done')
                break
            logging.info(f'{self.strategy_instance.strategy_code} : {len(pending)} buy orders pending...')
            time.sleep(1)
            count -= 1

    def sell(self, ticker, order_type, units, limit_price=None):
        return self.API.submit_order(
            symbol=ticker,
            qty=units,
            side='sell',
            type=order_type,
            time_in_force='day',
            client_order_id=self.strategy_instance.strategy_code+str(uuid.uuid1()))

    def bulkSell(self, sells, wait=30):
        sells = self.filterExistingPositions(sells, 'sell')
        for order in sells:
            try:
                logging.info(f'{self.strategy_instance.strategy_code} : submit(sell): {order}')
                self.sell(
                    order['symbol'],
                    'market',
                    order['qty'])
            except Exception as e:
                logging.error(f'{self.strategy_instance.strategy_code} : {e}')
        count = wait
        while count > 0 and len(sells) > 0:
            pending = self.API.list_orders()
            if len(pending) == 0:
                logging.info(f'{self.strategy_instance.strategy_code} : all sell orders done')
                break
            logging.info(f'{self.strategy_instance.strategy_code} : {len(pending)} sell orders pending...')
            time.sleep(1)
            count -= 1

    def trade(self, orders, wait=30):
        sells = [o for o in orders if o['side'] == 'sell']
        self.bulkSell(sells, wait=wait)

        buys = [o for o in orders if o['side'] == 'buy']
        self.bulkBuy(buys, wait=wait)

                        
    def get_prices(self, start, end=None, limit=50, tz='America/New_York'):
        '''
        Gets prices for list of symbols and returns a pandas df

                                        AAPL                    ...     BAC
                                    open     high      low  ...     low   close volume
        time                                                  ...
        2019-06-21 11:50:00-04:00  200.020  200.070  199.720  ...  28.420  28.435   6170
        2019-06-21 11:55:00-04:00  199.850  199.980  199.810  ...  28.410  28.435   6169
        '''

        timeframe=self.strategy_instance.params.get('timeframe')
        if not end:
            end = pd.Timestamp.now(tz=tz)

        # The maximum number of symbols we can request at once is 200.
        barset = None
        i = 0
        while i <= len(self.strategy_instance.params.get('assets')) - 1:
            temp_barset = self.API.get_barset(
                    self.strategy_instance.params.get('assets')[i:i+200],
                    timeframe,
                    limit=limit,
                    start=start,
                    end=end)
            if barset is None:
                barset = temp_barset
            else:
                barset.update(temp_barset)
            i += 200

        # Turns barset into a df
        return barset.df

    def beginTrading(self):
        logging.info(f'{self.strategy_instance.strategy_code} : start running')
        sleep = self.timeframe_map.get(self.strategy_instance.params.get('timeframe'))

        while True:
            clock = self.API.get_clock()
            if clock.is_open:
                if self.strategy_instance.params.get('needs_prices'):
                    logging.info(f'{self.strategy_instance.strategy_code}: Getting prices...')
                    start = pd.Timestamp.now() - pd.Timedelta(days=2)
                    prices_df = self.get_prices(start)

                    logging.info(f'{self.strategy_instance.strategy_code}: {prices_df.shape}')
                    
                    logging.info(f'{self.strategy_instance.strategy_code}: Getting orders...')
                    orders = self.strategy_instance.get_orders(prices_df=prices_df)
                else:
                    logging.info(f'{self.strategy_instance.strategy_code}: Getting orders...')
                    orders = self.strategy_instance.get_orders()

                logging.info(f'{self.strategy_instance.strategy_code}: orders {orders}')
                
                self.trade(orders)
                
                logging.info(self.strategy_instance.strategy_code)
                logging.info(self.API.get_account())
                logging.info(f'{self.strategy_instance.strategy_code}: done for {clock.timestamp}')
                logging.info(f'{self.strategy_instance.strategy_code}: waiting for {sleep}')
            else:
                time.sleep(60 * 10)
            time.sleep(60 * sleep)