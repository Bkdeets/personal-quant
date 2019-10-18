import os
import requests
import json

POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
KEY = os.getenv('APCA_API_KEY_ID')


def make_request(endpoint, ticker, params):
    url = POLYGON_BASE_URL + endpoint + ticker
    response = requests.get(
        url,
        params=params
    )
    return response.json()

def get_fundamentals(ticker, limit=2):
    endpoint = 'reference/financials/'
    params = {
        'apiKey': KEY,
        'limit': str(limit)
    }
    return make_request(endpoint, ticker, params)

def get_last_trade(ticker):
    endpoint = '/last/stocks/' 
    params = {
        'apiKey': KEY
    } 
    return make_request(endpoint, ticker, params)

def get_current_price(ticker):
    return get_last_trade(ticker)['last']['price']

def get_free_cash_flow(ticker):
    endpoint = '/reference/financials/' 
    params = {
        'apiKey': KEY
    } 
    return make_request(endpoint, ticker, params)['results'][0]['freeCashFlow']

def get_shares_outstanding(ticker):
    endpoint = '/reference/financials/' 
    params = {
        'apiKey': KEY
    } 
    return make_request(endpoint, ticker, params)['results'][0]['shares']

def get_dividends(ticker, limit=7):
    endpoint = '/reference/dividends/' 
    params = {
        'apiKey': KEY,
        'limit': str(limit)
    } 
    return make_request(endpoint, ticker, params)['results']
