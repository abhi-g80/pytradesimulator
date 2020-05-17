import quickfix as fix
import quickfix42 as fix42
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


class MarketDataClient(BaseApplication):
    def _generate_id(self):
        self.__count += 1
        return "TESTREQUEST" + str(self.__count)

    def set_logging(self, logger):
        self.logger = logger

    def onCreate(self, sessionID):
        self.__count = 0
        self.logger.info(f"Successfully created session {sessionID}.")
        return

    def onLogon(self, sessionID):
        self.logger.info(f"{sessionID} session successfully logged in.")
        return

    def onLogout(self, sessionID):
        self.logger.info(f"{sessionID} session successfully logged out.")
        return

    def toApp(self, message, sessionID):
        self.logger.debug(f"Sending {message} session {sessionID}")

    def fromApp(self, message, sessionID):
        self.logger.info(f"Got message {message} for {sessionID}.")
        self.show(message)

    def show(self, message):
        msgtype = fix.MsgType()
        message.getHeader().getField(msgtype)

        print(message.__str__().replace("\x01", "|"))

        _bids = []
        _asks = []
        _trades = []

        if msgtype.getValue() == "W":
            symbol = fix.Symbol()
            message.getField(symbol)

            instrument = symbol.getValue()

            entry_type = fix.MDEntryType()
            entry_px = fix.MDEntryPx()
            entry_size = fix.MDEntrySize()
            entries = fix.NoMDEntries()

            message.getField(entries)

            group = fix42.MarketDataSnapshotFullRefresh().NoMDEntries()

            for i in range(entries.getValue()):
                message.getGroup(i + 1, group)
                group.getField(entry_type)
                group.getField(entry_px)
                group.getField(entry_size)

                if entry_type.getValue() == "0":
                    _bids.append((entry_px.getValue(), entry_size.getValue()))
                elif entry_type.getValue() == "1":
                    _asks.append((entry_px.getValue(), entry_size.getValue()))
                elif entry_type.getValue() == "2":
                    _trades.append((entry_px.getValue(), entry_size.getValue()))

            book = Book(instrument, _bids, _asks, _trades)

            print(book)

    def market_data_request(self, sender_comp_id, target_comp_id, symbols):
        md_types = [fix.MDEntryType_BID, fix.MDEntryType_OFFER, fix.MDEntryType_TRADE]

        message = fix42.MarketDataRequest()

        header = message.getHeader()
        header.setField(fix.SenderCompID(sender_comp_id))
        header.setField(fix.TargetCompID(target_comp_id))

        message.setField(fix.MDReqID(self._generate_id()))
        message.setField(
            fix.SubscriptionRequestType(
                fix.SubscriptionRequestType_SNAPSHOT_PLUS_UPDATES
            )
        )
        message.setField(fix.MarketDepth(10))

        group = fix42.MarketDataRequest().NoMDEntryTypes()

        for md_type in md_types:
            group.setField(fix.MDEntryType(md_type))
            message.addGroup(group)

        group = fix42.MarketDataRequest().NoRelatedSym()

        for symbol in symbols:
            group.setField(fix.Symbol(symbol))
            message.addGroup(group)

        try:
            fix.Session.sendToTarget(message)
        except fix.SessionNotFound:
            raise Exception(f"No session found {message}, exiting...")
