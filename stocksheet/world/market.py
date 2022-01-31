import typing
from typing import Dict, Union
import math

import psycopg

from stocksheet.world.order import OrderDirection, OrderBuy, OrderSell
from stocksheet.world.stock import Stock
from stocksheet.entity.trader import Trader


class MarketOpenedError(Exception):
    pass


class MarketClosedError(Exception):
    pass


class StockPriceLimitError(Exception):
    pass

class Market:
    class PriceStepsizeFEval:
        def __init__(self):
            self._pricerange = list()
            self._steps = list()

        def compile(self, s: str):
            for p in s.split(' '):
                if p[0] == '/':
                    self._pricerange.append(int(p[1:]))
                else:
                    self._steps.append(int(p))
            pass

        def __call__(self, p, *args, **kwargs):
            for n, r in enumerate(p):
                if p < r:
                    return self._steps[n]
            return self._steps[-1]

    def price_round(self, price, roundfunc=math.floor):
        step = self._price_stepsize_f(price)
        return (roundfunc(price / step)) * step

    def price_variance(self, refprice: int):
        return (self.price_round(refprice + self.price_round(refprice * self._variancerate)),
                self.price_round(refprice - self.price_round(refprice * self._variancerate)))

    def __init__(self, dbinfo):
        self.__traders: Dict[typing.Hashable, Trader] = dict()
        self.__stocks: Dict[typing.Hashable, Stock] = dict()
        self._is_open = False
        self._timestamp = 0
        self.dbinfo = dbinfo

        self._price_stepsize_f = Market.PriceStepsizeFEval()  # Initial... won't work
        self._variancerate = 0.001   # too

    def open(self):
        """
        Start a day.
        :return:
        """
        if self._is_open:
            return


        async with await psycopg.AsyncConnection.connect(**self.dbinfo, autocommit=True) as dbconn:
            async with dbconn.cursor() as cur:
                await cur.execute("""SELECT value from config WHERE key = %s""", ('market_variancerate_float',), prepare=True)
                self._variancerate = float((await cur.fetchone())[0])
                await cur.execute("""SELECT value from config WHERE key = %s""", ('market_pricestepsize_fe',))
                self._price_stepsize_f.compile((await cur.fetchone())[0])

        for stock in self.__stocks.values():
            stock.open()
        self._is_open = True

    def close(self):
        """
        End a day.
        :return:
        """
        if not self._is_open:
            return



        self._is_open = False
        for stock in self.__stocks.values():
            stock.close()

    def trader_add(self, ident: typing.Hashable, trader: Trader):
        """
        When closed,
        Add a entity.
        :param ident:
        :param trader:
        :return:
        """
        if self._is_open:
            raise MarketOpenedError
        self.__traders[ident] = trader
        return ident

    def trader_get(self, ident: typing.Hashable):
        return self.__traders[ident]

    def trader_del(self, ident: typing.Hashable):
        """
        When closed,
        Delete the entity.
        :param ident:
        :return:
        """
        if self._is_open:
            raise MarketOpenedError
        s = self.__traders.pop(ident)
        del s

    def stock_list(self):
        """
        Show the stocks.
        :return:
        """
        return self.__stocks

    def stock_add(self, ticker: typing.Hashable):
        """
        When closed,
        Add a stock.
        :param ticker:
        :return:
        """
        if self._is_open:
            raise MarketOpenedError
        self.__stocks[ticker] = Stock(self)
        return self.stock_get(ticker)

    def stock_get(self, ticker: typing.Hashable):
        """
        Get a stock.
        :param ticker:
        :return:
        """
        return self.__stocks[ticker]

    def stock_del(self, ticker: typing.Hashable):
        """
        When closed,
        Delete a stock.
        :param ticker:
        :return:
        """
        if self._is_open:
            raise MarketOpenedError
        s = self.__stocks.pop(ticker)
        del s

    def order_put(self, traderident: typing.Hashable, ticker: typing.Hashable,
                  orderdirection: OrderDirection, count: int, price: Union[int, None] = None):
        """
        Trader에서 order을 넣을 것.
        :param traderident:
        :param ticker:
        :param orderdirection:
        :param count:
        :param price: 시장가 매매를 원할 시 None
        :return:
        """
        if not self._is_open:
            raise MarketClosedError

        stock = self.stock_get(ticker)
        price = self.price_round(price)

        if not (stock.lowlimit <= price <= stock.upplimit):
            raise StockPriceLimitError

        order = None
        if orderdirection == OrderDirection.Buy:
            order = OrderBuy(self, traderident, ticker, count, price, self._timestamp)
        elif orderdirection == OrderDirection.Sell:
            order = OrderSell(self, traderident, ticker, count, price, self._timestamp)
        self._timestamp += 1
        stock.order_put(order)
        order.activate()
        return order

    # def order_del(self):
    #    pass
