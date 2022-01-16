import typing
from typing import List, Dict

from stockstack.world.order import Order


class Trader:
    def __init__(self, market, traderident: typing.Hashable):
        self.market = market
        self.ident = traderident
        self.name = '(Unnamed Trader)'
        self.wallet_total = 0
        self.wallet_hold = 0
        self.history: List[Order] = list()
        self.stocks_total: Dict[typing.Hashable, int] = dict()
        self.stocks_hold: Dict[typing.Hashable, int] = dict()

    def wallet_cash_get(self):
        return self.wallet_total - self.wallet_hold_get()

    def wallet_hold_get(self):
        return self.wallet_hold

    def wallet_cash_take(self, amount):
        self.wallet_total -= amount

    def wallet_cash_hold(self, amount):
        self.wallet_hold += amount

    def wallet_hold_release(self, amount):
        self.wallet_hold -= amount

    def wallet_hold_take(self, amount):
        self.wallet_total -= amount
        self.wallet_hold -= amount

    def wallet_cash_give(self, amount):
        self.wallet_total += amount

    def stock_cash_get(self, ticker: typing.Hashable):
        t = self.stocks_total.get(ticker)
        return 0 if t is None else (t - self.stock_hold_get(ticker))

    def stock_hold_get(self, ticker: typing.Hashable):
        h = self.stocks_hold.get(ticker)
        return 0 if h is None else h

    def stock_cash_take(self, ticker: typing.Hashable, amount):
        self.stocks_total[ticker] -= amount

    def stock_cash_hold(self, ticker: typing.Hashable, amount):
        self.stocks_hold[ticker] += amount

    def stock_hold_release(self, ticker: typing.Hashable, amount):
        self.stocks_hold[ticker] -= amount

    def stock_hold_take(self, ticker: typing.Hashable, amount):
        self.stocks_total[ticker] -= amount
        self.stocks_hold[ticker] -= amount

    def stock_cash_give(self, ticker: typing.Hashable, amount):
        if ticker in self.stocks_total:
            self.stocks_total[ticker] += amount
        else:
            self.stocks_total[ticker] = amount

    def order(self, ticker: typing.Hashable, orderdirection, count, price):
        order = self.market.order_put(self.ident, ticker, orderdirection, count, price)
        self.history.append(order)
