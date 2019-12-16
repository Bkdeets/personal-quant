import os
import statistics
import math
from iexfinance.stocks import Stock
from ..wrappers import polygon as p
import pandas as pd

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []
IEX_TOKEN = os.getenv('IEX_TOKEN')

class Utility:

    def calc_eps_growth(self, fundamentals):
        changes = []
        for i in range(0,len(fundamentals)-1):
            previous = fundamentals[i].get('earningsPerBasicShare')
            current = fundamentals[i+1].get('earningsPerBasicShare')
            if previous and current and previous != 0:
                changes.append((current-previous)/previous)
        if len(changes) > 0:
            return statistics.mean(changes)
        return 0

    #CAPM
    def calc_cost_of_equity(self, fundamental):
        risk_free = self.get_risk_free_rate()
        beta = Stock(fundamental.get('ticker'), token=IEX_TOKEN).get_beta()
        equity_risk_premium = self.get_market_return() - self.get_risk_free_rate()
        return risk_free + (beta * equity_risk_premium)

    def calc_mos(self, current, expected):
        return 1-(current/expected)

    def get_risk_free_rate(self):
        return .015

    def get_market_return(self):
        return .1

    def calc_tax_rate(self, fundamental):
        earnings_before_tax = fundamental.get('earningsBeforeTax')
        tax_liability = fundamental.get('taxLiability')
        try:
            return tax_liability/earnings_before_tax
        except:
            return .15

    def get_cost_of_debt(self, fundamental):
        interest_paid = fundamental.get('interestExpense')
        total_debt = fundamental.get('debt')
        try:
            return interest_paid/total_debt
        except:
            return None

    def calc_wacc(self, fundamental):
        debt = fundamental.get('debt')
        dte = fundamental.get('debtToEquityRatio')
        cost_of_equity = self.calc_cost_of_equity(fundamental)
        cost_of_debt= self.get_cost_of_debt(fundamental)
        tax_rate = self.calc_tax_rate(fundamental)
        if debt and dte and cost_of_equity and cost_of_debt and tax_rate:
            equity = dte/debt
            value = debt + equity
            weight_of_debt = debt/value
            weight_of_equity = equity/value
            wacc = weight_of_debt*cost_of_debt*(1-tax_rate)+weight_of_equity*cost_of_equity
            return wacc
        return None

    def calc_dividend_growth_rate(self, ticker, limit=7):
        dividends = p.get_dividends(ticker, limit)
        changes = []
        for i in range(0,len(dividends)-1):
            previous = dividends[i].get('amount')
            current = dividends[i+1].get('amount')
            if previous and current:
                changes.append((current-previous)/previous)
            else:
                return None
        if len(dividends) > 0:
            return statistics.mean(changes)
        return None

    def calc_fcf_growth(self, fundamentals):
        changes = []
        if len(fundamentals) > 1:
            for i in range(0,len(fundamentals)-1):
                first = fundamentals[i].get('freeCashFlow')
                second = fundamentals[i+1].get('freeCashFlow')
                if first and second:
                    changes.append((second-first)/first)
        if len(changes) > 0:
            return statistics.mean(changes)
        else:
            return None

    def calc_avg_fcf(self, fundamentals):
        if len(fundamentals) > 0:
            fcfs = [fundamentals[i].get('freeCashFlow') for i in range(0,len(fundamentals)-1) if fundamentals[i].get('freeCashFlow')]
            if len(fcfs) > 0:
                return statistics.mean(fcfs)
        return None

    def calc_residual_income_growth(self, fundamentals):
        changes = []
        if len(fundamentals) > 1:
            for i in range(0,len(fundamentals)-1):
                previous = self.calc_residual_income(fundamentals[i])
                current = self.calc_residual_income(fundamentals[i+1])
                if previous and current and previous > 0:
                    changes.append((current-previous)/previous)
        if len(changes) > 0:
            return statistics.mean(changes)
        return None

    def calc_residual_income(self, fundamental):
        net_income = fundamental.get('netIncome')
        equity = fundamental.get('shareholdersEquity')
        cost_of_equity = self.calc_cost_of_equity(fundamental)
        if net_income and equity:
            return net_income - (equity * cost_of_equity)
        else:
            return None

    def getPositionsByStrategy(self, strategy_code, API):
        positions = API.list_positions()
        holdings = {p.symbol: p for p in positions}
        holding_symbols = list(holdings.keys())
        strategy_positions = []
        activities = API.get_activities(activity_types='FILL')
        for position in positions:
            for event in activities:
                    if event.symbol == position.symbol:
                        if event.id.startswith(strategy_code):
                            strategy_positions.append(position)
        return strategy_positions
    
    def getCurrentSide(self, strategy_code, ticker, API):
        positions = Utility().getPositionsByStrategy(strategy_code, API)
        if positions:
            position = [p for p in positions if p.symbol == ticker][0]
            return position.side
    
    def getPosition(self, strategy_code, ticker, API):
        positions = Utility().getPositionsByStrategy(strategy_code, API)
        position = [p for p in positions if p.symbol == ticker][0]
        return position

    def get_prices(self, start, timeframe, assets, API, end=None, limit=50, tz='America/New_York'):
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
        while i <= len(assets) - 1:
            if barset is None:
                barset = API.get_barset(
                    assets[i:i+200],
                    timeframe,
                    limit=limit,
                    start=start,
                    end=end)
            else:
                barset.update(
                    API.get_barset(
                        assets[i:i+200],
                        timeframe,
                        limit=limit,
                        start=start,
                        end=end))
            i += 200

        return barset.df

