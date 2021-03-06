# Copyright (C) 2013, Maxime Biais <maxime@biais.org>

from .marketnofiat import MarketNoFiat, TradeException, GetInfoException
from arbitrage import config
import time
import base64
import hmac
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import sys
import json
import requests

class PrivateBitstampBCH(MarketNoFiat):
    balance_url = "https://www.bitstamp.net/api/v2/balance/"
    buy_url = "https://www.bitstamp.net/api/v2/buy/bchbtc/"
    sell_url = "https://www.bitstamp.net/api/v2/sell/bchbtc/"

    def __init__(self):
        super().__init__()
        self.proxydict = None
        self.client_id = config.bitstamp_client_id
        self.api_key = config.bitstamp_api_key
        self.api_secret = config.bitstamp_api_secret
        self.get_info()        
        
    def _create_nonce(self):
        return int(time.time() * 1000000)

    def _send_request(self, url, params={}, extra_headers=None):
        headers = {
            'Content-type': 'application/json',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'
        }
        if extra_headers is not None:
            for k, v in extra_headers.items():
                headers[k] = v
        nonce = str(self._create_nonce())
        message = nonce + self.client_id + self.api_key
        if sys.version_info.major == 2:
            signature = hmac.new(self.api_secret, msg=message, digestmod=hashlib.sha256).hexdigest().upper()
        else:
            signature = hmac.new(str.encode(self.api_secret), msg=str.encode(message), digestmod=hashlib.sha256).hexdigest().upper()
        params['key'] = self.api_key
        params['signature'] = signature
        params['nonce'] = nonce
        #postdata = urllib.parse.urlencode(params).encode("utf-8")
        #req = urllib.request.Request(url, postdata, headers=headers)
        #print ("req=", postdata)
        #response = urllib.request.urlopen(req)
        response = requests.post(url, data=params, proxies=self.proxydict)
        #code = response.getcode()
        code = response.status_code
        if code == 200:
            #jsonstr = response.read().decode('utf-8')
            #return json.loads(jsonstr)
            return response.json()
        return None

    def _buy(self, amount, price):
        """Create a buy limit order"""
        params = {"amount": round(amount,8), "price": round(price,8)}
        response = self._send_request(self.buy_url, params)
        if "status" in response and "error" == response["status"]:
            raise TradeException(response["reason"])

    def _sell(self, amount, price):
        """Create a sell limit order"""
        params = {"amount": round(amount,8), "price": round(price,8)}
        response = self._send_request(self.sell_url, params)
        if "status" in response and "error" == response["status"]:
            raise TradeException(response["reason"])

    def get_info(self):
        """Get balance"""
        response = self._send_request(self.balance_url)
        if "status" in response and "error" == response["status"]:
            raise GetInfoException(response["reason"])
            return

        #print(json.dumps(response))            
        self.pair1_balance = float(response[str.lower(self.pair1_name)+"_available"])
        self.pair2_balance = float(response[str.lower(self.pair2_name)+"_available"])




if __name__ == "__main__":
    market = PrivateBitstampBCH()
    market.get_info()
    print(market)
