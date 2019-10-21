import os
import requests
import json

POLYGON_BASE_URL = 'https://api.polygon.io/'
KEY = os.getenv('APCA_API_KEY_ID')


def make_request(endpoint, ticker, params):
    url = POLYGON_BASE_URL + endpoint + ticker
    response = requests.get(
        url,
        params=params
    )
    return response.json()

def get_fundamentals(ticker, limit=2):
    endpoint = 'v2/reference/financials/'
    params = {
        'apiKey': KEY,
        'limit': str(limit),
        'type': 'Q'
    }
    return make_request(endpoint, ticker, params)

def get_last_trade(ticker):
    endpoint = '/v1/last/stocks/' 
    params = {
        'apiKey': KEY
    }
    return make_request(endpoint, ticker, params)

def get_current_price(ticker):
    return get_last_trade(ticker)['last']['price']

def get_free_cash_flow(ticker):
    endpoint = 'v2/reference/financials/'
    params = {
        'apiKey': KEY
    } 
    return make_request(endpoint, ticker, params)['results'][0]['freeCashFlow']

def get_shares_outstanding(ticker):
    endpoint = 'v2/reference/financials/'
    params = {
        'apiKey': KEY
    } 
    return make_request(endpoint, ticker, params)['results'][0]['shares']

def get_dividends(ticker, limit=7):
    endpoint = 'v2/reference/dividends/'
    params = {
        'apiKey': KEY,
        'limit': str(limit)
    } 
    return make_request(endpoint, ticker, params)['results']

def get_candle_by_date(ticker, date, limit=1):
    endpoint = 'v1/open-close/' + ticker + '/' + date
    params = {
        'apiKey': KEY,
        'limit': str(limit)
    } 
    url = POLYGON_BASE_URL + endpoint
    response = requests.get(
        url,
        params=params
    )
    return response.json()

def get_historical_quotes_from_date(ticker, start, limit=100):
    endpoint = 'v1/historic/quotes/' + ticker + '/' + start
    params = {
        'apiKey': KEY,
        'limit': str(limit)
    } 
    url = POLYGON_BASE_URL + endpoint
    response = requests.get(
        url,
        params=params
    )
    return response.json()

def get_aggregates(ticker, start, end, period='day', multiplier=1):
    endpoint = 'v2/aggs/ticker/'+ticker+'/range/'+str(multiplier)+'/'+period+'/'+start+'/'+end
    params = {
        'apiKey': KEY
    }
    url = POLYGON_BASE_URL + endpoint
    response = requests.get(
        url,
        params=params
    )
    return response.json()['results']

