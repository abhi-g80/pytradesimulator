import quickfix as fix

from .orderbook import Orderbook, Order, Trade

CLIENT_ORDER_IDs = {}

ORDER_IDs = {}
EXECUTION_IDs = {}

MARKETS = {}


class Message(fix.Message):
    def __str__(self):
        message = super().__str__()
        return message.replace("\x01", "|")


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


class MessageBroker(BaseApplication):
    def set_logging(self, logger):
        self.logger = logger

    def onCreate(self, sessionID):
        self.sessions = set()
        self.logger.info(f"Successfully created session {sessionID}.")
        return

    def onLogon(self, sessionID):
        self.sessions.add(sessionID.toString())
        self.logger.info(f"{sessionID} session successfully logged in.")
        return

    def onLogout(self, sessionID):
        self.sessions.discard(sessionID)
        self.logger.info(f"{sessionID} session successfully logged out.")
        return

    def fromApp(self, message, sessionID):
        responses = self.process(message, sessionID)
        
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

        if msgtype.getValue() == "D":
            self.logger.info(f"Incoming new order from {sessionID}. Processing...")
            responses = self.new_order_single(message, sessionID)
        elif msgtype.getValue() == "F":
            self.logger.info(f"Incoming cancel order from {sessionID}. Processing...")
            responses = self.order_cancel(message, sessionID)
        elif msgtype.getValue() == "G":
            self.logger.info(f"Incoming replace order from {sessionID}. Processing...")
            responses = self.order_replace(message, sessionID)

        return responses

    def _create_execution_report(
        self,
        symbol,
        price,
        quantity,
        side,
        client_order_id,
        order_status=fix.OrdStatus_NEW,
        exec_trans_type=fix.ExecTransType_NEW,
        exec_type=fix.ExecType_NEW,
        text=None,
        reject_reason=None,
    ):
        execution_report = Message()
        execution_report.getHeader().setField(fix.MsgType(fix.MsgType_ExecutionReport))

        execution_report.setField(
            fix.OrderID(self.generate_order_id(symbol.getValue()))
        )
        execution_report.setField(
            fix.ExecID(self.generate_execution_id(symbol.getValue()))
        )
        execution_report.setField(fix.OrdStatus(order_status))
        execution_report.setField(symbol)
        execution_report.setField(side)
        execution_report.setField(fix.CumQty(quantity.getValue()))
        execution_report.setField(fix.AvgPx(price.getValue()))
        execution_report.setField(fix.LastShares(quantity.getValue()))
        execution_report.setField(fix.LastPx(price.getValue()))
        execution_report.setField(client_order_id)
        execution_report.setField(quantity)
        execution_report.setField(fix.ExecTransType(exec_trans_type))
        execution_report.setField(fix.ExecType(exec_type))
        execution_report.setField(fix.LeavesQty(0))

        if text:
            execution_report.setField(fix.Text(text))

        if exec_type == fix.ExecType_REJECTED:
            execution_report.setField(fix.OrdRejReason(reject_reason))
        
        self.logger.debug(
                f"Created execution report (symbol, side, quantity, price): "
                f"{symbol} {side} {quantity} {price}."
        )

        return execution_report

    def __get_attributes(self, message):
        price = fix.Price()
        quantity = fix.OrderQty()
        symbol = fix.Symbol()
        side = fix.Side()
        client_order_id = fix.ClOrdID()

        message.getField(client_order_id)
        message.getField(side)
        message.getField(symbol)
        message.getField(price)
        message.getField(quantity)

        return (symbol, price, quantity, side, client_order_id)

    def _handle_trade(self, symbol, trade, sessionID):
        self.logger.info("Trade(s) executed.")

        # if trade.session.toString() != sessionID.toString():
        if trade.session.toString() not in self.sessions:
            self.logger.debug(f"Trade session {trade.session} and sessionID {sessionID} do not match, skipping trade")
            self.logger.debug(f"Dumping trade \n{trade}")
            return

        trade_side = "1" if trade.side == "b" else "2"

        execution_report = self._create_execution_report(
            symbol,
            fix.Price(trade.price),
            fix.LastQty(trade.quantity),
            fix.Side(trade_side),
            fix.ClOrdID(trade.order_id),
            order_status=fix.OrdStatus_FILLED,
            exec_type=fix.ExecType_FILL,
        )

        return execution_report

    def new_order_single(self, message, sessionID):
        symbol, price, quantity, side, client_order_id = self.__get_attributes(message)
        execution_report = None
        market = symbol.getValue()

        if market not in MARKETS:
            MARKETS[market] = Orderbook(market)

        order_side = "b" if side.getValue() == "1" else "s"
        order = Order(
            symbol.getValue(),
            price.getValue(),
            quantity.getValue(),
            order_side,
            client_order_id.getValue(),
            sessionID,
        )

        if sessionID.toString() in CLIENT_ORDER_IDs:
            CLIENT_ORDER_IDs[sessionID.toString()].append(client_order_id.getValue())
        else:
            CLIENT_ORDER_IDs[sessionID.toString()] = [client_order_id.getValue()]

        execution_reports = []

        MARKETS[market].process_incoming_order(order)
        self.logger.debug("Processed new order.")

        if MARKETS[market].trades.qsize() == 0:
            self.logger.debug("No trades.")
            execution_report = self._create_execution_report(
                symbol, price, quantity, side, client_order_id
            )
            execution_reports.append((sessionID, execution_report))
        else:
            while not MARKETS[market].trades.empty():
                trade = MARKETS[market].trades.get()
                execution_report = self._handle_trade(symbol, trade, sessionID)

                if execution_report:
                    execution_reports.append((trade.session, execution_report))

        return execution_reports

    def order_replace(self, message, sessionID):
        symbol, price, quantity, side, client_order_id = self.__get_attributes(message)

        orig_client_order_id = fix.OrigClOrdID()
        message.getField(orig_client_order_id)

        execution_report = None
        market = symbol.getValue()

        if market not in MARKETS:
            execution_report = self._create_execution_report(
                symbol, price, quantity, side, client_order_id,
                text=f"Symbol {symbol.getValue()} not found.",
                exec_type=fix.ExecType_REJECTED, reject_reason=fix.OrdRejReason_UNKNOWN_SYMBOL
            )
            return [(sessionID, execution_report)]

        self.logger.debug(CLIENT_ORDER_IDs)

        if (sessionID.toString() not in CLIENT_ORDER_IDs) or (orig_client_order_id.getValue() not in CLIENT_ORDER_IDs[sessionID.toString()]): 
            execution_report = self._create_execution_report(
                symbol, price, quantity, side, client_order_id,
                text=f"Client order ID {client_order_id.getValue()} not found.",
                exec_type=fix.ExecType_REJECTED,
                reject_reason=fix.OrdRejReason_UNKNOWN_ORDER
            )
            return [(sessionID, execution_report)]


        if sessionID.toString() in CLIENT_ORDER_IDs:
            CLIENT_ORDER_IDs[sessionID.toString()].append(client_order_id.getValue())
        else:
            CLIENT_ORDER_IDs[sessionID.toString()] = [client_order_id.getValue()]

        execution_reports = []

        order_side = "b" if side.getValue() == "1" else "s"
        order = Order(
            symbol.getValue(),
            price.getValue(),
            quantity.getValue(),
            order_side,
            client_order_id.getValue(),
            sessionID,
        )

        MARKETS[market]._replace_order(orig_client_order_id.getValue(), order)
        self.logger.debug("Processed replace order.")

        if MARKETS[market].trades.qsize() == 0:
            self.logger.debug("No trades.")
            execution_report = self._create_execution_report(
                symbol, price, quantity, side, client_order_id, exec_type=fix.ExecType_REPLACED
            )
            execution_reports.append((sessionID, execution_report))
        else:
            while not MARKETS[market].trades.empty():
                trade = MARKETS[market].trades.get()
                execution_report = self._handle_trade(symbol, trade, sessionID)

                if execution_report:
                    execution_reports.append((trade.session, execution_report))

        return execution_reports


    def order_cancel(self, message, sessionID):
        symbol, price, quantity, side, client_order_id = self.__get_attributes(message)
        execution_report = self._create_execution_report(
            symbol,
            price,
            quantity,
            side,
            client_order_id,
            order_status=fix.OrdStatus_CANCELLED,
            exec_type=fix.ExecType_CANCELLED,
        )

        return execution_report

    def generate_order_id(self, symbol):
        if symbol in ORDER_IDs:
            _id = ORDER_IDs[symbol]
        else:
            _id = 1

        ORDER_IDs[symbol] = _id + 1
        order_id = symbol + "_O_" + f"{_id:06}"

        return order_id

    def generate_execution_id(self, symbol):
        if symbol in EXECUTION_IDs:
            _id = EXECUTION_IDs[symbol]
        else:
            _id = 1

        EXECUTION_IDs[symbol] = _id + 1
        execution_id = symbol + "_E_" + f"{_id:06}"

        return execution_id
