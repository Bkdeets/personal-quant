from src.backtests.marsi_backtest import MarsiBacktest
from src.strategies.marsi import Marsi
import pandas as pd
import matplotlib.pyplot as plt
import alpaca_trade_api as tradeapi
import os
import pprint
class Account:
    daytrading_buying_power = 0
    cash = 0
    equity = 0
    portfolio_value = 0
    positions = []
    equities = []
    activities = []

class MockApi:
    def __init__(self, account):
        self.account = account

    def list_positions(self):
        return self.account.positions

    def get_activities(self, activity_types='FILL'):
        return self.account.activities

    def get_account(self):
        return self.account

class Activity:
    def __init__(self, symbol, id_code):
        self.symbol = symbol
        self.id = id_code

class Position:
    def __init__(self, symbol, side, qty, entryPrice):
        self.symbol = symbol
        self.side = side
        self.qty = qty
        self.entryPrice = entryPrice
    
class Backtester:
    API = tradeapi.REST(
        key_id=os.getenv('ALPACA_PAPER_KEY_ID'),
        secret_key=os.getenv('ALPACA_PAPER_KEY'),
        base_url='https://paper-api.alpaca.markets')

    def __init__(self, strategy_instance, account):
        self.strategy_instance = strategy_instance
        self.account = account
        self.currentPrice = 0
        self.trades = []
        self.po_map = {
            'sell':'short',
            'short':'sell',
            'buy':'long',
            'long':'buy'
        }

    def get_prices(self, start, end=None, limit=1000, tz='America/New_York'):
        timeframe=self.strategy_instance.params.get('timeframe')
        if not end:
            end = pd.Timestamp.now(tz=tz)
        # The maximum number of symbols we can request at once is 200.
        barset = None
        i = 0
        while i <= len(self.strategy_instance.params.get('assets')) - 1:
            if barset is None:
                barset = self.API.get_barset(
                    self.strategy_instance.params.get('assets')[i:i+200],
                    timeframe,
                    limit=limit,
                    start=start,
                    end=end)
            else:
                barset.update(
                    self.API.get_barset(
                        self.strategy_instance.params.get('assets')[i:i+200],
                        timeframe,
                        limit=limit,
                        start=start,
                        end=end))
            i += 200
        return barset.df

    def trade(self, orders):
        for order in orders:
            position = next(
                (position for position in self.account.positions if position.symbol == order.get('symbol')), 
                False
            )

            if(position and position.side != self.po_map.get(order.get('side'))):
                self.account.positions.remove(position)
                self.account.cash += self.currentPrice * order.get('qty')
                if position.side == 'short':
                    self.trades.append({
                        'action': 'so',
                        'price': self.currentPrice
                    })
                else:
                    self.trades.append({
                        'action': 'lo',
                        'price': self.currentPrice
                    })
                continue

            cost = self.currentPrice * order.get('qty')
            if(cost < self.account.daytrading_buying_power):
                position = Position(
                    order.get('symbol'),
                    self.po_map.get((order.get('side'))),
                    order.get('qty'),
                    self.currentPrice
                )
                self.account.positions.append(position)

                rem = self.account.cash - cost
                if(rem < 0):
                    self.account.cash -= cost + rem
                    self.account.daytrading_buying_power += rem
                else:
                    self.account.cash -= cost
                self.account.activities.append(Activity(position.symbol, self.strategy_instance.strategy_code))
                if position.side == 'short':
                    self.trades.append({
                        'action': 'si',
                        'price': self.currentPrice
                    })
                else:
                    self.trades.append({
                        'action': 'li',
                        'price': self.currentPrice
                    })
        
    def setEquity(self):
        value = 0
        for position in self.account.positions:
            if position.side == 'short':
                entryValue = position.entryPrice * position.qty
                value = (entryValue - (self.currentPrice * position.qty)) + entryValue
            else:
                value = self.currentPrice * position.qty
        self.account.equity = self.account.cash + value
        self.account.equities.append(self.account.equity)

    def getSLTPCloses(self):
        closes = []
        for position in self.account.positions:
            change = (self.currentPrice - position.entryPrice)/position.entryPrice
            if position.side == 'long' and abs(change) > self.strategy_instance.params.get('sl'):
                closes.append({
                    'symbol': position.symbol,
                    'qty': position.qty,
                    'side': 'sell'
                })
            elif position.side == 'short' and change > self.strategy_instance.params.get('sl'):
                closes.append({
                    'symbol': position.symbol,
                    'qty': position.qty,
                    'side': 'buy'
                })
        return closes
        
    def singleAssetBacktest(self, ticker):
        period = self.strategy_instance.params.get('period')
        smas = [0 for i in range(0, period)]
        rsis = [0 for i in range(0, period)]
        start = pd.Timestamp.now() - pd.Timedelta(days=2)
        prices_df = self.get_prices(start)
        prices = list(prices_df.get(ticker).get('close'))
        for i in range(period, len(prices)-1):
            self.currentPrice = prices[i]
            self.setEquity()
            df_chunk = prices_df.iloc[i - period:i+1,]
            orders = self.strategy_instance.get_orders(current_price=self.currentPrice, prices_df=df_chunk)
            smas.append(self.strategy_instance.sma.smas[-1])
            rsis.append(self.strategy_instance.rsi.rsis[-1])
            if orders:
                orders.extend(self.getSLTPCloses())
                print(orders)
                self.trade(orders)
            else:
                self.trades.append(None)
                
        # fig, axs = plt.subplots(2, 1)

        # # axs[0].plot(prices[period:])
        # # axs[0].plot(smas[period:])
        # # axs[1].plot(rsis[period:])
        # axs[0].plot(self.account.equities)


        for i in range(0,len(self.trades)):
            trade = self.trades[i]
            if trade:
                action = trade.get('action')
                price = trade.get('price')
                icon_map = {
                    'si': 'b+',
                    'so': 'r+',
                    'li': 'gx',
                    'lo': 'rx'
                }
                # axs[0].plot(i, price, icon_map.get(action))

        plt.show()


start = pd.Timestamp.now() - pd.Timedelta(days=50)
timeframe = 'minute'
symbols = [
        'MMM', 'ABT', 'ABBV', 'ACN', 'ATVI', 'AYI', 'ADBE', 'AMD', 'AAP', 'AES', 'AET', 'AMG', 'AFL', 'A', 'APD', 'AKAM', 
        'ALK', 'ALB', 'ARE', 'ALXN', 'ALGN', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALL', 'GOOGL', 'MO', 'AMZN', 'AEE', 'AAL', 'AEP', 'AXP', 'AIG', 'AMT', 'AWK', 
        'AMP', 'ABC', 'AME', 'AMGN', 'APH', 'APC', 'ADI', 'ANDV', 'ANSS', 'ANTM', 'AON', 'AOS', 'APA', 'AIV', 'AAPL', 'AMAT', 'APTV', 'ADM', 'ARNC', 'AJG', 
        'AIZ', 'T', 'ADSK', 'ADP', 'AZO', 'AVB', 'AVY', 'BHGE', 'BLL', 'BAC', 'BK', 'BAX', 'BBT', 'BDX', 'BRK.B', 'BBY', 'BIIB', 'BLK', 
        'HRB', 'BA', 'BKNG', 'BWA', 'BXP', 'BSX', 'BHF', 'BMY', 'AVGO', 'BF.B', 'CHRW', 'CA', 'COG', 'CDNS', 'CPB', 'COF', 'CAH', 'KMX', 'CCL', 'CAT', 'CBOE', 'CBRE', 'CBS', 'CELG', 
        'CNC', 'CNP', 'CTL', 'CERN', 'CF', 'SCHW', 'CHTR', 'CVX', 'CMG', 'CB', 'CHD', 'CI', 'XEC', 'CINF', 'CTAS', 'CSCO', 
        'C', 'CFG', 'CTXS', 'CLX', 'CME', 'CMS', 'KO', 'CTSH', 'CL', 'CMCSA', 'CMA', 'CAG', 'CXO', 'COP', 
        'ED', 'STZ', 'COO', 'GLW', 'COST', 'COTY', 'CCI', 'CSX', 'CMI', 'CVS', 'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DAL', 'XRAY', 'DVN', 'DLR', 'DFS', 'DISCA', 'DISCK', 
        'DISH', 'DG', 'DLTR', 'D', 'DOV', 'DWDP', 'DPS', 'DTE', 'DRE', 'DUK', 'DXC', 'ETFC', 'EMN', 'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ETR', 'EVHC', 'EOG', 'EQT', 'EFX', 'EQIX', 'EQR', 
        'ESS', 'EL', 'ES', 'RE', 'EXC', 'EXPE', 'EXPD', 'ESRX', 'EXR', 'XOM', 'FFIV', 'FB', 'FAST', 'FRT', 'FDX', 'FIS', 
        'FITB', 'FE', 'FISV', 'FLIR', 'FLS', 'FLR', 'FMC', 'FL', 'F', 'FTV', 'FBHS', 'BEN', 'FCX', 'GPS', 'GRMN', 'IT', 
        'GD', 'GE', 'GGP', 'GIS', 'GM', 'GPC', 'GILD', 'GPN', 'GS', 'GT', 'GWW', 'HAL', 'HBI', 'HOG', 'HRS', 'HIG', 'HAS', 'HCA', 'HCP', 'HP', 'HSIC', 'HSY', 'HES', 'HPE', 'HLT', 
        'HOLX', 'HD', 'HON', 'HRL', 'HST', 'HPQ', 'HUM', 'HBAN', 'HII', 'IDXX', 'INFO', 'ITW', 'ILMN', 'IR', 'INTC', 'ICE', 'IBM', 'INCY', 'IP', 'IPG', 'IFF', 'INTU', 'ISRG', 
        'IVZ', 'IPGP', 'IQV', 'IRM', 'JEC', 'JBHT', 'SJM', 'JNJ', 'JCI', 'JPM', 'JNPR', 'KSU', 'K', 'KEY', 'KMB', 'KIM', 'KMI', 'KLAC', 'KSS', 'KHC', 'KR', 'LB', 'LLL', 'LH', 'LRCX', 
        'LEG', 'LEN', 'LUK', 'LLY', 'LNC', 'LKQ', 'LMT', 'L', 'LOW', 'LYB', 'MTB', 'MAC', 'M', 'MRO', 'MPC', 'MAR', 'MMC', 'MLM', 'MAS', 'MA', 'MAT', 'MKC', 'MCD', 'MCK', 
        'MDT', 'MRK', 'MET', 'MTD', 'MGM', 'KORS', 'MCHP', 'MU', 'MSFT', 'MAA', 'MHK', 'TAP', 'MDLZ', 'MON', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MSCI', 'MYL', 'NDAQ', 'NOV', 'NAVI', 
        'NKTR', 'NTAP', 'NFLX', 'NWL', 'NFX', 'NEM', 'NWSA', 'NWS', 'NEE', 'NLSN', 'NKE', 'NI', 'NBL', 'JWN', 'NSC', 'NTRS', 'NOC', 'NCLH', 'NRG', 'NUE', 'NVDA', 'ORLY', 'OXY', 'OMC', 'OKE', 'ORCL', 'PCAR', 'PKG', 'PH', 'PAYX', 'PYPL', 'PNR', 'PBCT', 
        'PEP', 'PKI', 'PRGO', 'PFE', 'PCG', 'PM', 'PSX', 'PNW', 'PXD', 'PNC', 'RL', 'PPG', 'PPL', 'PX', 'PFG', 'PG', 'PGR', 'PLD', 'PRU', 'PEG', 'PSA', 'PHM', 'PVH', 'QRVO', 'PWR', 'QCOM', 'DGX', 'RRC', 'RJF', 'RTN', 'O', 'RHT', 'REG', 'REGN', 'RF', 
        'RSG', 'RMD', 'RHI', 'ROK', 'COL', 'ROP', 'ROST', 'RCL', 'CRM', 'SBAC', 'SCG', 'SLB', 'STX', 'SEE', 'SRE', 'SHW', 'SPG', 'SWKS', 'SLG', 'SNA', 'SO', 'LUV', 'SPGI', 'SWK', 'SBUX', 'STT', 'SRCL', 'SYK', 'STI', 'SIVB', 'SYMC', 'SYF', 'SNPS', 'SYY', 
        'TROW', 'TTWO', 'TPR', 'TGT', 'TEL', 'FTI', 'TXN', 'TXT', 'TMO', 'TIF', 'TWX', 'TJX', 'TMK', 'TSS', 'TSCO', 'TDG', 'TRV', 'TRIP', 'FOXA', 'FOX', 'TSN', 'UDR', 'ULTA', 'USB', 'UAA', 'UA', 'UNP', 'UAL', 'UNH', 'UPS', 'URI', 'UTX', 'UHS', 'UNM', 'VFC', 
        'VLO', 'VAR', 'VTR', 'VRSN', 'VRSK', 'VZ', 'VRTX', 'VIAB', 'V', 'VNO', 'VMC', 'WMT', 'WBA', 'DIS', 'WM', 'WAT', 'WEC', 'WFC', 'WELL', 'WDC', 'WU', 'WRK', 'WY', 'WHR', 'WMB', 'WLTW', 'WYN', 'WYNN', 'XEL', 'XRX', 'XLNX', 'XL', 'XYL', 'YUM', 'ZBH', 'ZION', 'ZTS'
    ]

symbols = ['AAPL']
account = Account()
account.cash = 25000
account.equity = 25000
account.daytrading_buying_power = 100000
mockapi = MockApi(account)

params = {
    'sma':{
        'level': .005
    },
    'rsi':{
        'topLevel': 65,
        'bottomLevel': 35
    },
    'sl':.05,
    'period':30,
    'assets': symbols,
    'timeframe': 'minute',
    'API': mockapi
}

for symbol in symbols:
    strategy = Marsi('backtest', params)
    backtester = Backtester(strategy, account)
    backtester.singleAssetBacktest(symbol)
    print(backtester.account.cash)
    pprint.pprint(backtester.account.equities)
    plt.plot(backtester.account.equities)
    plt.show()