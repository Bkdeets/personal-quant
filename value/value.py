import os
import statistics
import math
from iexfinance.stocks import Stock
import PolygonWrapper as pw 

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []
IEX_TOKEN = os.getenv('IEX_TOKEN')

def calc_tax_rate(fundamental):
    earnings_before_tax = fundamental.get('earningsBeforeTax')
    tax_liability = fundamental.get('taxLiability')
    try:
        return tax_liability/earnings_before_tax
    except:
        return .15

def calc_eps_growth(fundamentals):
    changes = [0]
    for i in range(0,len(fundamentals)-2):
        previous = fundamentals[i].get('earningsPerBasicShare')
        current = fundamentals[i+1].get('earningsPerBasicShare')
        if previous and current and previous != 0:
            changes.append((current-previous)/previous)
    return statistics.mean(changes)

def get_risk_free_rate():
    return .015

def get_market_return():
    return .1

def get_cost_of_debt(fundamentals):
    interest_paid = fundamentals[0].get('interestExpense')
    total_debt = fundamentals[0].get('debt')
    try:
        return interest_paid/total_debt
    except:
        return None

def calc_mos(current, expected):
    return 1-(current/expected)

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
    dividends = pw.get_dividends(ticker, limit)
    changes = []
    for i in range(0,len(dividends)-2):
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
    for i in range(0,len(fundamentals)-2):
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
    for i in range(0,len(fundamentals)-2):
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

#CAPM
def calc_cost_of_equity(fundamental):
    risk_free = get_risk_free_rate()
    beta = Stock(fundamental.get('ticker'), token=IEX_TOKEN).get_beta()
    equity_risk_premium = get_market_return() - get_risk_free_rate()
    return risk_free + beta * equity_risk_premium

# Divident Discount Model
def calc_dd_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    growth_rate = calc_dividend_growth_rate(ticker)
    divs = pw.get_dividends(ticker)
    discount_rate = calc_cost_of_equity(fundamentals[0])
    current_price = pw.get_current_price(ticker)
    if len(divs) > 0 and growth_rate and ticker and discount_rate and current_price:
        d1 = divs[0].get('amount') * (1 + growth_rate)
        exp_price = d1/(discount_rate-growth_rate)
        if exp_price > 0:
            print(growth_rate)
            print(d1)
            print(discount_rate)
            print(current_price)
            print(exp_price)
            return calc_mos(current_price, exp_price)
    return None

# Free Cash Flow Model
def calc_fcf_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    growth = calc_fcf_growth(fundamentals)
    wacc = calc_wacc(fundamentals)
    cf = calc_avg_fcf(fundamentals)
    shares_outstanding = pw.get_shares_outstanding(ticker)
    current_price = pw.get_current_price(ticker)
    if current_price and shares_outstanding and cf and wacc and growth and ticker:
        enterprise_value = 0
        for i in range(0,5):
            numerator = cf * math.pow(1+growth,i)
            denominator = 1 + wacc
            enterprise_value += numerator/denominator
        terminal_value = cf/(wacc-growth)
        enterprise_value += terminal_value
        exp_price = enterprise_value/shares_outstanding
        return calc_mos(current_price, exp_price)
    return None

# Graham Dodd Model
def calc_gd_model(fundamentals):
    eps = fundamentals[0].get('earningsPerBasicShareUSD')
    ticker = fundamentals[0].get('ticker')
    current_price = pw.get_current_price(ticker)
    growth = calc_eps_growth(fundamentals)
    if eps and growth and current_price:
        exp_price = (eps * (7 + growth) * .015)/.03
        return calc_mos(current_price, exp_price)
    return None

# Residual Income Model
def calc_ri_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    ri = calc_residual_income(fundamentals[0])
    ri_growth = calc_residual_income_growth(fundamentals)
    cost_of_equity = calc_cost_of_equity(fundamentals[0])
    current_price = pw.get_current_price(ticker)
    price_to_book = fundamentals[0].get('priceToBookValue')
    shares_outstanding = pw.get_shares_outstanding(ticker)
    if shares_outstanding and price_to_book and current_price and cost_of_equity and ri_growth and ri:
        enterprise_value = 0
        for i in range(0,5):
            numerator = ri * math.pow(1+ri_growth,i)
            denominator = math.pow(1 + cost_of_equity,i)
            enterprise_value += numerator/denominator
        enterprise_value += (price_to_book)*(1/current_price)
        exp_price = enterprise_value/shares_outstanding
        return calc_mos(current_price, exp_price)
    return None

def calc_models(fundamentals):
    gd = calc_gd_model(fundamentals)
    ri = calc_ri_model(fundamentals)
    fcf = calc_fcf_model(fundamentals)
    dd = calc_dd_model(fundamentals)
    models = [gd,ri,fcf,dd]
    res = []
    for model in models:
        if model:
            res.append(model)
    if len(res) > 0:
        return res
    return None
    

def get_check_for_buys(level, assets):
    to_buy = []
    for ticker in assets:
        fundamentals = pw.get_fundamentals(ticker, limit=7)['results'][::-1]
        dte = fundamentals[0].get('debtToEquityRatio')
        ptb = fundamentals[0].get('priceToBookValue')
        if len(fundamentals) > 0 and dte <= 1.5 and ptb < 1:
            if calc_eps_growth(fundamentals) > 0:
                print(ticker + " passed... Running valuation models")
                models = calc_models(fundamentals)
                if models:
                    margin_of_safety = (sum(models))/len(models)
                    print(ticker + " -- " + str(margin_of_safety))
                    if margin_of_safety > level:
                        to_buy.append((ticker, margin_of_safety))
        else:
            continue
    return to_buy.sort(key=lambda tup: tup[1])

def get_check_for_buy(level, ticker):
    to_buy = []
    fundamentals = pw.get_fundamentals(ticker, limit=7)['results']
    dte = fundamentals[0].get('debtToEquityRatio')
    ptb = fundamentals[0].get('priceToBookValue')
    eps_growth = calc_eps_growth(fundamentals)
    if len(fundamentals) > 0 and dte <= 1.5 and ptb < 1 and eps_growth and eps_growth > 0:
            print(ticker + " passed... Running valuation models")
            models = calc_models(fundamentals)
            if models:
                margin_of_safety = (sum(models))/len(models)
                print(ticker + " -- " + str(margin_of_safety) + models)
                if margin_of_safety > level:
                    to_buy.append((ticker, margin_of_safety))
    return to_buy

def get_check_for_buy_backtest(level, ticker, fundamentals):
    to_buy = (False,0)
    dte = fundamentals[0].get('debtToEquityRatio')
    ptb = fundamentals[0].get('priceToBookValue')
    if len(fundamentals) > 4 and dte and dte <= 1.5 and ptb and ptb < 1:
        if calc_eps_growth(fundamentals) > 0:
            print(ticker + " passed... Running valuation models")
            models = calc_models(fundamentals)
            if models:
                margin_of_safety = (sum(models))/len(models)
                print(ticker + " -- " + str(margin_of_safety))
                print(models)
                if margin_of_safety > level:
                    to_buy = (True, margin_of_safety)
    return to_buy