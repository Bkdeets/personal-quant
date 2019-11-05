import os
import statistics
import math
from iexfinance.stocks import Stock
from . import polygon as pw 

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []
IEX_TOKEN = os.getenv('IEX_TOKEN')

def calc_eps_growth(fundamentals):
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
def calc_cost_of_equity(fundamental):
    risk_free = get_risk_free_rate()
    beta = Stock(fundamental.get('ticker'), token=IEX_TOKEN).get_beta()
    equity_risk_premium = get_market_return() - get_risk_free_rate()
    return risk_free + (beta * equity_risk_premium)

def calc_mos(current, expected):
    return 1-(current/expected)

def get_risk_free_rate():
    return .015

def get_market_return():
    return .1

def calc_tax_rate(fundamental):
    earnings_before_tax = fundamental.get('earningsBeforeTax')
    tax_liability = fundamental.get('taxLiability')
    try:
        return tax_liability/earnings_before_tax
    except:
        return .15

def get_cost_of_debt(fundamentals):
    interest_paid = fundamentals[0].get('interestExpense')
    total_debt = fundamentals[0].get('debt')
    try:
        return interest_paid/total_debt
    except:
        return None

def calc_wacc(fundamentals):
    debt = fundamentals[0].get('debt')
    dte = fundamentals[0].get('debtToEquityRatio')
    cost_of_equity = calc_cost_of_equity(fundamentals[0])
    cost_of_debt= get_cost_of_debt(fundamentals)
    tax_rate = calc_tax_rate(fundamentals[0])
    if debt and dte and cost_of_equity and cost_of_debt and tax_rate:
        equity = dte/debt
        value = debt + equity
        weight_of_debt = debt/value
        weight_of_equity = equity/value
        wacc = weight_of_debt*cost_of_debt*(1-tax_rate)+weight_of_equity*cost_of_equity
        return wacc
    return None

def calc_dividend_growth_rate(ticker, limit=7):
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

def calc_fcf_growth(fundamentals):
    changes = [0]
    for i in range(0,len(fundamentals)-1):
        first = fundamentals[i].get('freeCashFlow')
        second = fundamentals[i+1].get('freeCashFlow')
        if first and second:
            changes.append((second-first)/first)
    return statistics.mean(changes)

def calc_avg_fcf(fundamentals):
    fcfs = [fundamentals[i].get('freeCashFlow') for i in range(0,len(fundamentals)-1) if fundamentals[i].get('freeCashFlow')]
    return statistics.mean(fcfs)

def calc_residual_income_growth(fundamentals):
    changes = []
    for i in range(0,len(fundamentals)-1):
        previous = calc_residual_income(fundamentals[i])
        current = calc_residual_income(fundamentals[i+1])
        if previous and current and previous > 0:
            changes.append((current-previous)/previous)
    if len(changes) > 0:
        return statistics.mean(changes)
    return None

def calc_residual_income(fundamental):
    net_income = fundamental.get('netIncome')
    equity = fundamental.get('shareholdersEquity')
    cost_of_equity = calc_cost_of_equity(fundamental)
    if net_income and equity:
        return net_income - (equity * cost_of_equity)
    else:
        return None