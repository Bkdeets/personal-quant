from abc import ABC, abstractmethod
import alpaca_trade_api as tradeapi
import os
import logging

class AStrategy(ABC):
    def __init__(self, env, params):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        self.NY = 'America/New_York'
        self.env = env

        if env == 'test' or env == 'backtest':
            self.API = params.get('API')
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
        self.env = env
        self.params = params
        self.dataUtility = DataUtility(self)
        
    @abstractmethod
    def get_orders(self, position_size=.05, prices_df=[]):
        return []
