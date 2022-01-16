import typing
from typing import TYPE_CHECKING
from abc import abstractmethod
from enum import Enum

if TYPE_CHECKING:
    from market import Market


class NotEnoughMoneyError(Exception):
    pass


class OrderDirection(Enum):
    Sell = 1
    Buy = 2


class Order:
    def __init__(self, market: 'Market', traderident: typing.Hashable, ticker, price, count, timestamp):
        self.market = market
        self.traderident = traderident
        self.ticker = ticker
        self.direction = None
        self.price = price
        self.count = count
        self.timestamp = timestamp
        self.__active = False

    def activate(self):
        if self.count > 0:
            self.__active = True

    @abstractmethod
    def trade(self, price, count):
        pass

    @abstractmethod
    def close(self):
        pass

    def is_active(self):
        return (self.count > 0) and self.__active

    def is_end(self):
        return self.count == 0


class OrderBuy(Order):
    def __init__(self, market, traderident, ticker, price, count, timestamp):
        super().__init__(market, traderident, ticker, price, count, timestamp)
        self.direction = OrderDirection.Buy
        self.holding_amount = 0

    def activate(self):
        trader = self.market.trader_get(self.traderident)
        self.holding_amount = self._holding_per_1_calc()
        trader.wallet_cash_hold(self.holding_amount * self.count)
        super().activate()

    def _holding_per_1_calc(self):
        if self.price is None:
            return self.market.stock_get(self.ticker).upplimit
        else:
            return self.price

    def trade(self, price, count):
        self.count -= count
        trader = self.market.trader_get(self.traderident)
        trader.wallet_hold_take(count * price)
        trader.wallet_hold_release(count * (self.holding_amount - price))
        trader.stock_cash_give(self.ticker, count)

    def close(self):
        self.market.trader_get(self.traderident).wallet_hold_release(self.count * self.holding_amount)


class OrderSell(Order):
    def __init__(self, market, traderident, ticker, price, count, timestamp):
        super().__init__(market, traderident, ticker, price, count, timestamp)
        self.direction = OrderDirection.Sell

    def activate(self):
        trader = self.market.trader_get(self.traderident)
        trader.stock_cash_hold(self.ticker, self.count)
        super().activate()

    def trade(self, price, count):
        self.count -= count
        trader = self.market.trader_get(self.traderident)
        trader.stock_hold_take(self.ticker, count)
        trader.wallet_give(count * price)

    def close(self):
        self.market.trader_get(self.traderident).stock_hold_release(self.ticker, self.count)
