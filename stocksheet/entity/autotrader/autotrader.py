import typing

from stocksheet.entity.trader import Trader


class AutoTrader(Trader):
    def __init__(self, market, traderident: typing.Hashable):
        super().__init__(market, traderident)
