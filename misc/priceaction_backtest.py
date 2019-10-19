import backtrader as bt
import pandas as pd
import Wrapper
from sr_indicator import SuppprtResistanceIndicator


class PriceActionBacktest(bt.Strategy):
    params = (
        ('sl', -.005),
        ('tp', .005),
        ('lookback', 15),
        ('printlog', True),
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function for this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None

        self.sr = SuppprtResistanceIndicator(
            self.datas[0], lookback=self.params.lookback)
        

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

        # Write down: no pending order
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % self.dataclose[0])

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        print(self.sr[0])
        # Check if we are in the market
        if not self.position:
            # Not yet ... we MIGHT BUY if ...
            
            if self.sr[0] == 1:
                self.log('BUY CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
            elif self.sr[0] == -1:
                self.log('SHORT CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()

        else:
            isBuy = False
            if self.position.size > 0: 
                isBuy = True 

            if isBuy and self.sr == -1:
                self.log('EXIT CREATE, %.2f' % self.dataclose[0])
                self.order = self.sell()
            elif not isBuy and self.sr == 1:
                self.log('EXIT CREATE, %.2f' % self.dataclose[0])
                self.order = self.buy()
                    

    def stop(self):
        self.log('(Lookback %2d) Ending Value %.2f' %
                 (self.params.lookback, self.broker.getvalue()), doprint=True)


    def checkBuy(self):
        print(self.data)
        lookback = self.data


if __name__ == '__main__':

    # Create a cerebro entity
    cerebro = bt.Cerebro()

    cerebro.addstrategy(PriceActionBacktest)

    # Get shtuff from Alpaca via a wrapper
    start = pd.Timestamp.now() - pd.Timedelta(days=365)
    dataframe = Wrapper.getData(['BAC'], '15Min', start)

    # Convert column tuples to strings
    for i in range(len(dataframe.columns.values)):
        dataframe.columns.values[i] = dataframe.columns.values[i][1]

    # Create a Data Feed
    data = bt.feeds.PandasData(dataname=dataframe)

    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(10000.0)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=10)

    # Set the commission
    cerebro.broker.setcommission(commission=0.0)

    print("here1")
    # Run over everything
    res = cerebro.run(maxcpus=1)
    print(res)
    print("done runnning")

    cerebro.plot()