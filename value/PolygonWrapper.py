import os
import requests
import json

POLYGON_BASE_URL = os.getenv('POLYGON_BASE_URL')
KEY = os.getenv('APCA_API_KEY_ID')

def get_fundamentals(ticker, limit=1):
    endpoint = 'reference/financials/' + ticker
    url = POLYGON_BASE_URL + endpoint
    response = requests.get(
        url,
        params={
            'apiKey': KEY,
            'limit': str(limit)
        }
    )
    return response.json()
