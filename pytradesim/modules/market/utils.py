import quickfix as fix
from prettytable import PrettyTable


class Book:
    def __init__(self, symbol, bids, asks, trades):
        self.symbol = symbol
        self.bids = bids
        self.asks = asks
        self.trades = trades

    def __str__(self):
        table = PrettyTable()

        if len(self.asks) > len(self.bids):
            diff = len(self.asks) - len(self.bids)
            while diff:
                self.bids.append(("Empty", "Empty"))
                diff -= 1
        elif len(self.bids) > len(self.asks):
            diff = len(self.bids) - len(self.asks)
            while diff:
                self.asks.append(("Empty", "Empty"))
                diff -= 1

        table.add_column("bid_prc, bid_qty", self.bids)
        table.add_column("ask_prc, ask_qty", self.asks)

        print(f"Symbol: {self.symbol}")
        print(table)

        for trade in self.trades:
            print(f"Trade {self.symbol}, {trade[1]}@{trade[0]}.")

        return ""


class BaseApplication(fix.Application):
    def onCreate(self, sessionID):
        return

    def onLogon(self, sessionID):
        return

    def onLogout(self, sessionID):
        return

    def toAdmin(self, message, sessionID):
        return

    def fromAdmin(self, message, sessionID):
        return

    def toApp(self, message, sessionID):
        return

    def fromApp(self, message, sessionID):
        return
