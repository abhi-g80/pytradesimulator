import quickfix as fix
import quickfix42 as fix42


class Book:
    def __init__(self, symbol, bids, asks, trades):
        self.symbol = symbol
        self.bids = bids
        self.asks = asks
        self.trades = trades


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


class MarketDataAdapter(BaseApplication):
    def set_logging(self, logger):
        self.logger = logger

    def onCreate(self, sessionID):
        self.sessions = set()
        self.clients = {}
        self.logger.info(f"Successfully created sessions {sessionID}.")

    def onLogon(self, sessionID):
        self.sessions.add(sessionID)
        self.logger.info(f"{sessionID} successfully logged in.")

    def onLogout(self, sessionID):
        self.sessions.discard(sessionID)
        self.logger.info(f"{sessionID} session successfully logged out.")
        return

    def toApp(self, message, sessionID):
        self.logger.debug(f"Sending via {sessionID} : {message}")

    def fromApp(self, message, sessionID):
        responses = self.process(message, sessionID)

        if responses:
            for response in responses:
                if isinstance(response[1], fix.Message):
                    try:
                        msg = response[1].__str__()
                        msg = msg.replace("\x01", "|")
                        self.logger.debug(f"Sending: {msg}")
                        fix.Session.sendToTarget(response[1], response[0])
                    except fix.SessionNotFound as error:
                        raise fix.SessionNotFound(error)
        return

    def process(self, message, sessionID):
        msgtype = fix.MsgType()
        message.getHeader().getField(msgtype)

        self.logger.debug(f"Processing message: {message}")
        if msgtype.getValue() == "V":
            self.logger.info(f"Incoming MD request {sessionID}. Processing...")
            responses = self.market_data_request(message, sessionID)

        return responses

    def __add_client(self, message, sessionID):
        no_of_symbols = fix.NoRelatedSym()
        no_related_symbols = fix42.MarketDataRequest().NoRelatedSym()
        message.getField(no_of_symbols)
        symbol = fix.Symbol()

        for i in range(no_of_symbols.getValue()):
            message.getGroup(i + 1, no_related_symbols)
            no_related_symbols.getField(symbol)
            sym = symbol.getValue()

            self.logger.debug(f"Got request for symbol {sym} from {sessionID}.")

            if sym in self.clients:
                self.clients[sym].append(sessionID)
            else:
                self.clients[sym] = [sessionID]

    def __remove_client(self, message, sessionID):
        no_of_symbols = fix.NoRelatedSym()
        no_related_symbols = fix42.MarketDataRequest.NoRelatedSym()
        message.getField(no_of_symbols)
        symbol = fix.Symbol()

        for i in range(no_of_symbols):
            message.getGroup(i + 1, no_related_symbols)
            no_related_symbols.getField(symbol)
            sym = symbol.getValue()

            if sym in self.clients:
                self.clients[sym].remove(sessionID)

    def market_data_request(self, message, sessionID):
        subscription_request_type = fix.SubscriptionRequestType()
        message.getField(subscription_request_type)

        if subscription_request_type.getValue() == "2":
            # remove client
            self.__remove_client(message, sessionID)
        else:
            # add client
            self.__add_client(message, sessionID)

    def dispatch(self, book):
        symbol = book.symbol
        bids = book.bids
        asks = book.asks
        trades = book.trades

        message = fix42.MarketDataSnapshotFullRefresh()

        message.setField(fix.Symbol(symbol))

        group = fix42.MarketDataSnapshotFullRefresh().NoMDEntries()

        if bids:
            for i in range(len(bids)):
                group.setField(fix.MDEntryType(fix.MDEntryType_BID))
                group.setField(fix.MDEntryPx(float(bids[i][0])))
                group.setField(fix.MDEntrySize(float(bids[i][1])))
                message.addGroup(group)

        if asks:
            for i in range(len(asks)):
                group.setField(fix.MDEntryType(fix.MDEntryType_OFFER))
                group.setField(fix.MDEntryPx(float(asks[i][0])))
                group.setField(fix.MDEntrySize(float(asks[i][1])))
                message.addGroup(group)

        if trades:
            for i in range(len(trades)):
                group.setField(fix.MDEntryType(fix.MDEntryType_TRADE))
                group.setField(fix.MDEntryPx(float(trades[i][0])))
                group.setField(fix.MDEntrySize(float(trades[i][1])))
                message.addGroup(group)

        self.logger.debug(f"Clients {self.clients}")

        print(message.__str__().replace("\x01", "|"))

        if symbol in self.clients:
            for session in self.clients[symbol]:
                fix.Session.sendToTarget(message, session)
