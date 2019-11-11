import os
import statistics
import math
from iexfinance.stocks import Stock
from ..wrappers import polygon as p 
from ..utility.utility import Utility

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []
IEX_TOKEN = os.getenv('IEX_TOKEN')

# fundamentals go old to new

# Divident Discount Model
def calc_dd_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    growth_rate = Utility().calc_dividend_growth_rate(ticker)
    if growth_rate and growth_rate > 0:
        try:
            divs = p.get_dividends(ticker)
        except:
            return None
        if len(divs) > 0:
            discount_rate = Utility().calc_cost_of_equity(fundamentals[-1])
            try:
                current_price = p.get_current_price(ticker)
            except:
                return None
            if discount_rate and growth_rate < discount_rate and current_price:
                d1 = divs[-1].get('amount') * (1 + growth_rate)
                exp_price = d1/(discount_rate-growth_rate)
                if exp_price > 0:
                    return Utility().calc_mos(current_price, exp_price)
    return None

# Free Cash Flow Model
def calc_fcf_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    growth = Utility().calc_fcf_growth(fundamentals)
    if growth and growth > 0:
        wacc = Utility().calc_wacc(fundamentals[-1])
        cf = Utility().calc_avg_fcf(fundamentals)
        if wacc and cf and cf > 0 and growth < wacc:
            try:
                shares_outstanding = p.get_shares_outstanding(ticker)
                current_price = p.get_current_price(ticker)
            except:
                return None
            if current_price and shares_outstanding:
                enterprise_value = 0
                for i in range(0,len(fundamentals)):
                    pv = cf * math.pow(1+growth,i)
                    enterprise_value += pv
                terminal_value = cf/(wacc-growth)
                enterprise_value += terminal_value
                present_value = enterprise_value/math.pow(1+wacc,len(fundamentals))
                exp_price = present_value/shares_outstanding
                return Utility().calc_mos(current_price, exp_price)
    return None

# Graham Dodd Model
def calc_gd_model(fundamentals):
    eps = fundamentals[-1].get('earningsPerBasicShareUSD')
    ticker = fundamentals[0].get('ticker')
    try:
        current_price = p.get_current_price(ticker)
    except:
        return None
    growth = Utility().calc_eps_growth(fundamentals)
    if eps and growth and current_price and growth > 0:
        exp_price = ((100*eps) * (7 + (growth*100)) * 1.5)/3
        return Utility().calc_mos(current_price, exp_price)
    return None

# Residual Income Model
def calc_ri_model(fundamentals):
    ticker = fundamentals[0].get('ticker')
    ri = Utility().calc_residual_income(fundamentals[-1])
    ri_growth = Utility().calc_residual_income_growth(fundamentals)
    if ri and ri_growth and ri_growth > 0:
        cost_of_equity = Utility().calc_cost_of_equity(fundamentals[-1])
        if cost_of_equity:
            try:
                current_price = p.get_current_price(ticker)
                shares_outstanding = p.get_shares_outstanding(ticker)
            except:
                return None
            price_to_book = fundamentals[-1].get('priceToBookValue')
            if shares_outstanding and price_to_book and current_price:
                enterprise_value = 0
                for i in range(1,len(fundamentals)):
                    numerator = ri * math.pow(1+ri_growth,i)
                    denominator = math.pow(1+cost_of_equity,i)
                    enterprise_value += numerator/denominator
                book_value = current_price/price_to_book
                enterprise_value += book_value*shares_outstanding
                exp_price = enterprise_value/shares_outstanding
                return Utility().calc_mos(current_price, exp_price)
    return None

def calc_models(fundamentals):
    # dcf
    gd = calc_gd_model(fundamentals)
    ri = calc_ri_model(fundamentals)
    fcf = calc_fcf_model(fundamentals)
    dd = calc_dd_model(fundamentals)
    models = [gd,ri,fcf,dd]
    res = []
    for model in models:
        if model and -5 < model < 5:
            res.append(model)
    if len(res) > 0:
        return res
    return None
    

def get_check_for_buys(level, assets):
    to_buy = []
    for ticker in assets:
        try:
            fundamentals = p.get_fundamentals(ticker, limit=7)
        except:
            continue
        if fundamentals.get('results'):
            fundamentals = fundamentals.get('results')[::-1]
            if len(fundamentals) > 0:
                dte = fundamentals[-1].get('debtToEquityRatio')
                ptb = fundamentals[-1].get('priceToBookValue')
                if dte <= 1.5 and ptb < 1:
                    if Utility().calc_eps_growth(fundamentals) > 0:
                        print(ticker + " passed... Running valuation models")
                        models = calc_models(fundamentals)
                        if models:
                            margin_of_safety = (sum(models))/len(models)
                            if margin_of_safety > level:
                                print(ticker + " -- " + str(margin_of_safety))
                                to_buy.append((ticker, margin_of_safety))
    return sorted(to_buy, key=lambda tup: tup[1])

def get_check_for_buy_backtest(level, ticker, fundamentals):
    to_buy = (False,0)
    dte = fundamentals[-1].get('debtToEquityRatio')
    ptb = fundamentals[-1].get('priceToBookValue')
    if len(fundamentals) > 4 and dte and dte <= 1.5 and ptb and ptb < 1:
        if Utility().calc_eps_growth(fundamentals) > 0:
            print(ticker + " passed... Running valuation models")
            models = calc_models(fundamentals)
            if models:
                margin_of_safety = (sum(models))/len(models)
                print(ticker + " -- " + str(margin_of_safety))
                if margin_of_safety > level:
                    to_buy = (True, margin_of_safety)
    return to_buy