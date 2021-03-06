import time
import urllib.request
import urllib.error
import urllib.parse
import logging
import sys
from arbitrage import config
from arbitrage.fiatconverter import FiatConverter
from arbitrage.utils import log_exception
from arbitrage.observers.telegram import send_message

class Market(object):
    def __init__(self, currency):
        self.name = self.__class__.__name__
        self.currency = currency
        self.depth_updated = 0
        self.update_rate = 0.5
        self.isWebsocket = False
        self.shouldReportWebsocketTimeout = False
        if currency == "BTC":
            self.fiat = False
        else:
            self.fiat = True
            self.fc = FiatConverter()
            self.fc.update()

    def get_depth(self):
        timediff = time.time() - self.depth_updated
        if timediff > self.update_rate:
            self.ask_update_depth()
        timediff = time.time() - self.depth_updated
        if timediff > config.market_expiration_time:
            _str = 'Market: %s order book is expired' % self.name
            logging.warn(_str)
            send_message(_str)
            self.depth = {'asks': [{'price': 0, 'amount': 0}], 'bids': [
                {'price': 0, 'amount': 0}]}
            raise Exception('get depth timeout.')
        return self.depth

    def convert_to_usd(self):
        if self.currency == "USD":
            return
        for direction in ("asks", "bids"):
            for order in self.depth[direction]:
                order["price"] = self.fc.convert(order["price"], self.currency, "USD")

    def ask_update_depth(self):
        try:
            self.update_depth()
            if self.fiat:
                self.convert_to_usd()
            self.depth_updated = time.time()
            self.shouldReportWebsocketTimeout = True
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            logging.error("HTTPError, can't update market: %s" % self.name)
            log_exception(logging.DEBUG)
        except Exception as e:
            if not self.isWebsocket:   
                logging.error("Can't update market: %s - %s" % (self.name, str(e)))
                log_exception(logging.DEBUG)
            else:
                #don't repeat report
                if self.shouldReportWebsocketTimeout:
                    logging.error(str(e))
                    self.shouldReportWebsocketTimeout = False
                


    def get_ticker(self):
        depth = self.get_depth()
        res = {'ask': 0, 'bid': 0}
        if len(depth['asks']) > 0 and len(depth["bids"]) > 0:
            res = {'ask': depth['asks'][0],
                   'bid': depth['bids'][0]}
        return res

    ## Abstract methods
    def update_depth(self):
        pass

    def buy(self, price, amount):
        pass

    def sell(self, price, amount):
        pass
