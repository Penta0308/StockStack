import abc


class Wallet:
    def __init__(self, trader):
        self.__trader = trader

    def wallet_get(self):
        pass

    def wallet_take(self, amount):
        pass

    def wallet_give(self, amount):
        pass
