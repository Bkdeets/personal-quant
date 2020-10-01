from src.strategies.marsi import Marsi
from src.strategies.longshort import LongShort
from src.strategies.longshortML import LongShortML
import pandas as pd
import matplotlib.pyplot as plt
import alpaca_trade_api as tradeapi
import os
import pprint

class Account:
    cash = 0
    equity = 0
    buying_power = 0
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

    def documentTrade(self, exited_position, isExit):
        if exited_position.side == 'short':
            position_side = 's'
        else:
            position_side = 'l'
        if isExit:
            trade_direction = 'o'
        else:
            trade_direction = 'i'
        
        action = position_side + trade_direction
        
        self.trades.append({
            'action': action,
            'price': self.currentPrice
        })

    def trade(self, orders):
        for order in orders:
            matched_position = False
            for position in self.account.positions:
                if position.symbol == order.get('symbol'):
                    matched_position = position
            isExit = matched_position and matched_position.side != self.po_map.get(order.get('side'))
            if matched_position and isExit:
                self.account.positions.remove(matched_position)
                if matched_position.side == 'long':
                    self.account.cash += self.currentPrice * matched_position.qty
                else:
                    entryValue = matched_position.entryPrice * matched_position.qty
                    exitValue = self.currentPrice * matched_position.qty
                    value = entryValue - exitValue
                    self.account.cash += (value + entryValue)
                self.documentTrade(matched_position, isExit)
            elif not isExit and not matched_position:
                cost = self.currentPrice * order.get('qty')
                if cost < self.account.buying_power:
                    position = Position(
                        order.get('symbol'),
                        self.po_map.get((order.get('side'))),
                        order.get('qty'),
                        self.currentPrice)
                    self.account.positions.append(position)
                    if cost > self.account.cash: 
                        self.account.buying_power -= self.account.cash
                        cost -= self.account.cash
                        self.account.buying_power -= cost
                    else:
                        self.account.cash -= cost
                        self.account.buying_power -= cost
                    
                    self.account.activities.append(Activity(position.symbol, self.strategy_instance.strategy_code))
                    self.documentTrade(position, False)
        
    def setEquity(self):
        value = 0
        for position in self.account.positions:
            if position.side == 'short' or position.side == 'sell':
                entryValue = position.entryPrice * position.qty
                currentValue = self.currentPrice * position.qty
                value = (entryValue - currentValue) + entryValue
            else:
                value = self.currentPrice * position.qty
        self.account.equity = self.account.cash + value
        self.account.equities.append(self.account.equity)

    def getSLTPCloses(self):
        closes = []
        for position in self.account.positions:
            change = (self.currentPrice - position.entryPrice)/position.entryPrice
            if position.side == 'long' and change < -self.strategy_instance.params.get('sl'):
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
    
    def closeOpenPositions(self):
        closes = []
        for position in self.account.positions:
            change = (self.currentPrice - position.entryPrice)/position.entryPrice
            if position.side == 'long':
                close_dir = 'sell'
            elif position.side == 'short':
                close_dir = 'buy'
            closes.append({
                'symbol': position.symbol,
                'qty': position.qty,
                'side': close_dir
            })
        self.trade(closes)
        
    def syncBuyingPowerAndCash(self):
        self.account.buying_power = self.account.cash

    def multiAssetBacktest(self, plotResults):
        period = self.strategy_instance.params.get('period')
        start = pd.Timestamp.now() - pd.Timedelta(days=50)
        prices_df = self.get_prices(start)
        for (asset in prices_df):
            prices = list(prices_df.get(asset).get('close'))
            self.prices = prices
            if plotResults:
                plt.plot(prices)
                plt.show()
            for i in range(period, len(prices)-1):
                self.currentPrice = prices[i]
                self.setEquity()
                if self.strategy_instance.params.get('closeEOD'):
                    self.closeOpenPositions()

                df_chunk = prices_df.iloc[i - period:i+1,]
                orders = self.strategy_instance.get_orders(current_price=self.currentPrice, prices_df=df_chunk)
                if orders:
                    orders.extend(self.getSLTPCloses())
                    print(f'orders: {orders}')
                    print(f'positions: {self.account.positions}')
                    self.trade(orders)
                else:
                    self.trades.append(None)
                self.syncBuyingPowerAndCash()
                
        fig, axs = plt.subplots(2, 1)

        axs[0].plot(prices[period:])

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
                axs[0].plot(i, price, icon_map.get(action))
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
account.buying_power = account.cash
mockapi = MockApi(account)

params = {
    'sl': .5,
    'period': 50,
    'rsi': {
        'period': 20
    },
    'assets': symbols,
    'timeframe': 'day',
    'API': mockapi,
    'closeEOD': False,
    'posSize': .1
}

for symbol in symbols:
    strategy = LongShortML('backtest', params)
    backtester = Backtester(strategy, account)
    backtester.singleAssetBacktest(symbol)
    print((backtester.account.equities[-1]-backtester.account.equities[0])/backtester.account.equities[0])
    #pprint.pprint(backtester.account.equities)

    fig, axs = plt.subplots(2, 1)
    axs[0].plot(backtester.prices)
    axs[1].plot(backtester.account.equities)
    plt.show()