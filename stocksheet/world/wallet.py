class Wallet:
    def __init__(self, tid):
        self.__traderident = tid

    def wallet_get(self, dbconn):
        return self.wallet_total - self.wallet_hold_get()

    def wallet_take(self, amount):
        self.wallet_total -= amount

    def wallet_give(self, amount):
        self.wallet_total += amount
