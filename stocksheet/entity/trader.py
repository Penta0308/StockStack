import typing
from typing import List, Dict

from stocksheet.world.order import Order
from stocksheet.world.wallet import Wallet


class Trader:
    def __init__(self, market, traderident: typing.Hashable):
        self.market = market
        self.ident = traderident
        self.name = "(Unnamed)"
        self.wallet = Wallet(self.ident)

    def stock_get(self, ticker: str, dbconn):
        pass

    def order(self, ticker: typing.Hashable, orderdirection, count, price):
        order = self.market.order_put(self.ident, ticker, orderdirection, count, price)
