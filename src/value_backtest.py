
from datetime import datetime, timedelta
import polygon as p

import os
import statistics
import math
from iexfinance.stocks import Stock
import utility as u

KEY = os.getenv('APCA_API_SECRET_KEY')
ID = os.getenv('APCA_API_KEY_ID')
BASE_URL = os.getenv('APCA_API_BASE_URL')
POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
S_AND_P_500 = []
IEX_TOKEN = os.getenv('IEX_TOKEN')

# fundamentals go old to new

# Divident Discount Model
def calc_dd_model(fundamentals, current_price):
    ticker = fundamentals[0].get('ticker')
    growth_rate = u.calc_dividend_growth_rate(ticker)
    if growth_rate and growth_rate > 0:
        divs = p.get_dividends(ticker)
        if len(divs) > 0:
            discount_rate = u.calc_cost_of_equity(fundamentals[-1])
            if discount_rate and growth_rate < discount_rate and current_price:
                d1 = divs[-1].get('amount') * (1 + growth_rate)
                exp_price = d1/(discount_rate-growth_rate)
                if exp_price > 0:
                    return u.calc_mos(current_price, exp_price)
    return None

# Free Cash Flow Model
def calc_fcf_model(fundamentals, current_price):
    ticker = fundamentals[0].get('ticker')
    growth = u.calc_fcf_growth(fundamentals)
    if growth and growth > 0:
        wacc = u.calc_wacc(fundamentals)
        cf = u.calc_avg_fcf(fundamentals)
        if wacc and cf and cf > 0 and growth < wacc:
            shares_outstanding = fundamentals[-1].get('shares')
            if current_price and shares_outstanding:
                enterprise_value = 0
                for i in range(0,len(fundamentals)):
                    pv = cf * math.pow(1+growth,i)
                    enterprise_value += pv
                terminal_value = cf/(wacc-growth)
                enterprise_value += terminal_value
                present_value = enterprise_value/math.pow(1+wacc,len(fundamentals))
                exp_price = present_value/shares_outstanding
                return u.calc_mos(current_price, exp_price)
    return None

# Graham Dodd Model
def calc_gd_model(fundamentals, current_price):
    eps = fundamentals[-1].get('earningsPerBasicShareUSD')
    ticker = fundamentals[0].get('ticker')
    growth = u.calc_eps_growth(fundamentals)
    if eps and growth and current_price and growth > 0:
        exp_price = ((100*eps) * (7 + (growth*100)) * 1.5)/3
        return u.calc_mos(current_price, exp_price)
    return None

# Residual Income Model
def calc_ri_model(fundamentals, current_price):
    ticker = fundamentals[0].get('ticker')
    ri = u.calc_residual_income(fundamentals[-1])
    ri_growth = u.calc_residual_income_growth(fundamentals)
    if ri and ri_growth and ri_growth > 0:
        cost_of_equity = u.calc_cost_of_equity(fundamentals[-1])
        if cost_of_equity:
            price_to_book = fundamentals[-1].get('priceToBookValue')
            shares_outstanding = fundamentals[-1].get('shares')
            if shares_outstanding and price_to_book and current_price:
                enterprise_value = 0
                for i in range(1,len(fundamentals)):
                    numerator = ri * math.pow(1+ri_growth,i)
                    denominator = math.pow(1+cost_of_equity,i)
                    enterprise_value += numerator/denominator
                book_value = current_price/price_to_book
                enterprise_value += book_value*shares_outstanding
                exp_price = enterprise_value/shares_outstanding
                return u.calc_mos(current_price, exp_price)
    return None

def calc_models(fundamentals, price):
    # dcf
    gd = calc_gd_model(fundamentals, price)
    ri = calc_ri_model(fundamentals, price)
    fcf = calc_fcf_model(fundamentals, price)
    ## dd = calc_dd_model(fundamentals, price)
    dd=None
    models = [gd,ri,fcf, dd]
    res = []
    for model in models:
        if model and -5 < model < 5:
            res.append(model)
    if len(res) > 0:
        return res
    return None

def get_check_for_buy_backtest(level, ticker, fundamentals, price):
    to_buy = (False,0)
    dte = fundamentals[-1].get('debtToEquityRatio')
    ptb = fundamentals[-1].get('priceToBookValue')
    if len(fundamentals) > 4 and dte and dte <= 1.5 and ptb and ptb < 1:
        if u.calc_eps_growth(fundamentals) > 0:
            print(ticker + " passed... Running valuation models")
            models = calc_models(fundamentals, price)
            if models:
                margin_of_safety = (sum(models))/len(models)
                print(ticker + " -- " + str(margin_of_safety))
                if margin_of_safety > level:
                    to_buy = (True, margin_of_safety)
    return to_buy

def iterate_prices(ticker, entry_price, start, sl, tp):
    print("iterating prices")
    last_price = 0
    last_date = 0
    end = datetime.strptime(start, '%Y-%m-%d') + timedelta(days=90)
    end = end.strftime('%Y-%m-%d')
    candles = p.get_aggregates(ticker, start, end)
    for i in range(0,len(candles)-1):
        date = datetime.strptime(start, '%Y-%m-%d') + timedelta(days=i)
        date = date.strftime('%Y-%m-%d')
        last_date = date
        candle = candles[i]
        if candle.get('c'):
            current_price = candle['c']
            last_price = current_price
            change = (current_price - entry_price) / entry_price
            if change > 0:
                if change > tp:
                    print("hit tp")
                    # return (current_price, date)
            elif abs(change) > sl:
                print("hit sl")
                return (current_price, date)
    print("90 days ran out -- exiting")
    return (last_price, last_date)
        
def backtest(level, ticker):
    balance = 1000

    # Old to new
    fundamentals = p.get_fundamentals(ticker, limit=50)['results'][::-1] #Quarterly -- 10 years
    if len(fundamentals) > 0:
        exit_date = fundamentals[0]['calendarDate']
        for i in range(5, len(fundamentals)-1):
            fundamental = fundamentals[i]
            fund_window = fundamentals[i-5:i]
            ticker = fundamental['ticker']
            date = fundamental['calendarDate']
            datetime_date = datetime.strptime(date, '%Y-%m-%d')
            datetime_exit_date = datetime.strptime(exit_date, '%Y-%m-%d')
            if datetime_date >= datetime_exit_date:
                price = 0
                for j in range(0,3):
                    date = datetime_date + timedelta(days=j)
                    date = date.strftime('%Y-%m-%d')
                    price = p.get_candle_by_date(ticker, date).get('close')
                    if price:
                        break
                is_buy = get_check_for_buy_backtest(level, ticker, fund_window, price)
                if price and is_buy[0]:
                    print(str(price) + " is buy")
                    tp = .5
                    if is_buy[1] > tp:
                        tp = 1
                    exit_info = iterate_prices(ticker, price, date, .4, tp)
                    print(exit_info)
                    if exit_info:
                        exit_date = exit_info[1]
                        change = (exit_info[0] - price)/price
                        print(change)
                        balance = balance * (1+change)        
    return balance
            
def backtest_list(level, tickers):
    total = 10000
    res = []
    for ticker in tickers:
        balance = backtest(level, ticker)
        total += balance - 1000
        ch = (balance - 1000) / 1000
        res.append((ticker, balance, ch))
        print(ticker + '  ' + str(balance) + '  ' + str(ch))
    print(str(total) + "  change = " + str((total-10000)/10000))

print(backtest_list(.3,[
        'ALLE', 'ANTM', 'APA', 'ADM', 'BLK', 'HRB', 'BSX', 'DHI', 'DISH', 'DG', 'DLTR', 'D', 'DOV', 
        'DWDP', 'DPS', 'DTE', 'DRE', 'EXPE', 'FL', 'F', 'FCX', 'MCD', 'MGM', 'MU', 'MHK', 'TAP'
    ]))


