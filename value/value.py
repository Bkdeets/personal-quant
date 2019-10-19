from . import PolygonWrapper as pw 
import os
import statistics
import math
from iexfinance.stocks import Stock

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []

def calc_tax_rate(fundamental):
    earnings_before_tax = fundamental['earningsBeforeTax']
    tax_liability = fundamental['taxLiability']
    return tax_liability/earnings_before_tax

def calc_eps_growth(fundamentals):
    changes = []
    for i in range(0,len(fundamentals)-2):
        current = fundamentals[i]['earningsPerBasicShare']
        previous = fundamentals[i+1]['earningsPerBasicShare']
        changes.append((current-previous)/previous)
    return statistics.mean(changes)

def get_risk_free_rate():
    return .015

def get_market_return():
    return .1

def get_cost_of_debt(fundamentals):
    interest_paid = fundamentals[0]['interestExpense']
    total_debt = fundamentals[0]['debt']
    return interest_paid/total_debt

def calc_tax_rate(fundamental):
    # ticker = fundamental['ticker']
    # stock = Stock(ticker).get_financials()
    # print(stock)
    # tax_paid = 'EffectiveIncomeTaxRateContinuingOperations'
    return .15

def calc_mos(current, expected):
    return 1-(current/expected)

def calc_wacc(fundamentals):
    debt = fundamentals[0]['debt']
    equity = fundamentals[0]['debtToEquityRatio']/debt
    value = debt + equity
    cost_of_equity = calc_cost_of_equity(fundamentals[0])
    cost_of_debt= get_cost_of_debt(fundamentals)
    weight_of_debt = debt/value
    weight_of_equity = equity/value
    tax_rate = calc_tax_rate(fundamentals[0])
    wacc = weight_of_debt*cost_of_debt*(1-tax_rate)+weight_of_equity*cost_of_equity
    return wacc

def calc_dividend_growth_rate(ticker, limit=7):
    dividends = pw.get_dividends(ticker, limit)
    changes = []
    for i in range(0,len(dividends)-2):
        current = dividends[i]['amount']
        previous = dividends[i+1]['amount']
        changes.append((current-previous)/previous)
    if len(dividends) > 0:
        return statistics.mean(changes)
    return 0

def calc_fcf_growth(fundamentals):
    changes = []
    for i in range(0,len(fundamentals)-2):
        current = fundamentals[i]['freeCashFlow']
        previous = fundamentals[i+1]['freeCashFlow']
        changes.append((current-previous)/previous)
    return statistics.mean(changes)

def calc_avg_fcf(fundamentals):
    fcfs = [fundamentals[i]['freeCashFlow'] for i in range(0,len(fundamentals)-1)]
    return statistics.mean(fcfs)

def calc_residual_income_growth(fundamentals):
    changes = []
    for i in range(0,len(fundamentals)-2):
        current = calc_residual_income(fundamentals[i])
        previous = calc_residual_income(fundamentals[i+1])
        changes.append((current-previous)/previous)
    return statistics.mean(changes)

def calc_residual_income(fundamental):
    net_income = fundamental['netIncome']
    equity = fundamental['shareholdersEquity']
    cost_of_equity = calc_cost_of_equity(fundamental)
    return net_income - (equity * cost_of_equity)

#CAPM
def calc_cost_of_equity(fundamental):
    risk_free = get_risk_free_rate()
    beta = Stock(fundamental['ticker']).get_beta()
    equity_risk_premium = get_market_return() - get_risk_free_rate()
    return risk_free + beta * equity_risk_premium

# Divident Discount Model
def calc_dd_model(fundamentals):
    growth_rate = calc_dividend_growth_rate(fundamentals[0]['ticker'])
    d1 = pw.get_dividends(fundamentals[0]['ticker'])[0]['amount'] * (1 + growth_rate)
    discount_rate = calc_cost_of_equity(fundamentals[0])
    exp_price = d1/(discount_rate-growth_rate)
    current_price = pw.get_current_price(fundamentals[0]['ticker'])
    if exp_price > 0:
        return calc_mos(current_price, exp_price)
    return 0

# Free Cash Flow Model
def calc_fcf_model(fundamentals):
    growth = calc_fcf_growth(fundamentals)
    wacc = calc_wacc(fundamentals)
    cf = calc_avg_fcf(fundamentals)
    shares_outstanding = pw.get_shares_outstanding(fundamentals[0]['ticker'])
    enterprise_value = 0
    for i in range(0,5):
        numerator = cf * math.pow(1+growth,i)
        denominator = 1 + wacc
        enterprise_value += numerator/denominator
    terminal_value = cf/(wacc-growth)
    enterprise_value += terminal_value
    exp_price = enterprise_value/shares_outstanding
    current_price = pw.get_current_price(fundamentals[0]['ticker'])
    return calc_mos(current_price, exp_price)

# Graham Dodd Model
def calc_gd_model(fundamentals):
    eps = fundamentals[0]['earningsPerBasicShareUSD']
    growth = calc_eps_growth(fundamentals)
    exp_price = (eps * (7 + growth) * 4)/3.5
    current_price = pw.get_current_price(fundamentals[0]['ticker'])
    return calc_mos(current_price, exp_price)

# Residual Income Model
def calc_ri_model(fundamentals):
    ticker = fundamentals[0]['ticker']
    ri = calc_residual_income(fundamentals[0])
    ri_growth = calc_residual_income_growth(fundamentals)
    cost_of_equity = calc_cost_of_equity(fundamentals[0])
    enterprise_value = 0
    for i in range(0,5):
        numerator = ri * math.pow(1+ri_growth,i)
        denominator = math.pow(1 + cost_of_equity,i)
        enterprise_value += numerator/denominator
    current_price = pw.get_current_price(ticker)
    enterprise_value += (fundamentals[0]['priceToBookValue'])*(1/current_price)
    exp_price = enterprise_value/pw.get_shares_outstanding(ticker)
    return calc_mos(current_price, exp_price)

def calc_models(fundamentals):
    ri = calc_ri_model(fundamentals)
    fcf = calc_fcf_model(fundamentals)
    gd = calc_gd_model(fundamentals)
    if len(pw.get_dividends(fundamentals[0]['ticker'])) > 0:
        dd = calc_dd_model(fundamentals)
        return [dd,ri,fcf,gd]
    return [ri,fcf,gd]
    

def get_check_for_buys(level, assets):
    to_buy = []
    for ticker in assets:
        fundamentals = pw.get_fundamentals(ticker, limit=7)['results']
        try:
            if len(fundamentals) > 0 and fundamentals[0]['debtToEquityRatio'] <= 1.5 and fundamentals[0]['priceToBookValue'] < 1:
                if calc_eps_growth(fundamentals) > 0:
                    print(ticker + " passed... Running valuation models")
                    models = calc_models(fundamentals)
                    margin_of_safety = (sum(models))/len(models)
                    print(ticker + " -- " + str(margin_of_safety))
                    if margin_of_safety > level:
                        to_buy.append((ticker, margin_of_safety))
        except Exception as e: 
            print(e)
            continue
    return to_buy.sort(key=lambda tup: tup[1])

def get_check_for_buy(level, ticker):
    to_buy = []
    fundamentals = pw.get_fundamentals(ticker, limit=7)['results']
    try:
        if len(fundamentals) > 0 and fundamentals[0]['debtToEquityRatio'] <= 1.5 and fundamentals[0]['priceToBookValue'] < 1:
            if calc_eps_growth(fundamentals) > 0:
                print(ticker + " passed... Running valuation models")
                models = calc_models(fundamentals)
                margin_of_safety = (sum(models))/len(models)
                print(ticker + " -- " + str(margin_of_safety))
                if margin_of_safety > level:
                    to_buy.append((ticker, margin_of_safety))
    except Exception as e: 
        print(e)
    return to_buy