#!/usr/bin/env python

import quickfix as fix
import quickfix42 as fix42
import time
import click
import logging
import configparser
from time import sleep

from datetime import datetime

from modules.utils import LogFormat, setup_logging, Message


ORDERS = {}


class BaseApplication(fix.Application):
    def onCreate(self, sessionID):
        return

    def onLogon(self, sessionID):
        return

    def onLogout(self, sessionID):
        return

    def toAdmin(self, message, sessionID):
        self.sessionID = sessionID
        return

    def fromAdmin(self, message, sessionID):
        return

    def toApp(self, message, sessionID):
        return

    def fromApp(self, message, sessionID):
        return


ORDER_TABLE = {}


class Client(BaseApplication):
    def set_logging(self, logger):
        self.logger = logger

    def onCreate(self, sessionID):
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
        self.process(message, sessionID)

    def process(self, message, sessionID):
        self.logger.debug("Processing message.")
        msgtype = fix.MsgType()
        exectype = fix.ExecType()
        message.getHeader().getField(msgtype)
        message.getField(exectype)

        if msgtype.getValue() == "8":
            if exectype.getValue() == "2":
                self.logger.info("Trade received.")
                (
                    symbol,
                    price,
                    quantity,
                    side,
                    client_order_id,
                    trade_exec_id,
                    order_status,
                ) = self.__get_attributes(message)
                self.logger.info(
                    f"Trade: {trade_exec_id}, {client_order_id} {symbol} {quantity}@{price} {side}"
                )
            elif exectype.getValue() == "0":
                self.logger.info("Order placed successfully.")
                (
                    symbol,
                    price,
                    quantity,
                    side,
                    client_order_id,
                    exec_id,
                    order_status,
                ) = self.__get_attributes(message)

                ORDERS[client_order_id.getValue()] = [symbol, price, quantity, side]

                self.logger.info(
                    f"Order: {exec_id}, {client_order_id} {symbol} {quantity}@{price} {side}"
                )
            elif exectype.getValue() == "5":
                self.logger.info("Order replaced successfully.")
                (
                    symbol,
                    price,
                    quantity,
                    side,
                    client_order_id,
                    exec_id,
                    order_status,
                ) = self.__get_attributes(message)

                ORDERS[client_order_id.getValue()] = [symbol, price, quantity, side]

                self.logger.info(
                    f"Order: {exec_id}, {client_order_id} {symbol} {quantity}@{price} {side}"
                )

    def __get_attributes(self, message):
        price = fix.LastPx()
        quantity = fix.LastQty()
        symbol = fix.Symbol()
        side = fix.Side()
        client_order_id = fix.ClOrdID()
        exec_id = fix.ExecID()
        order_status = fix.OrdStatus()

        message.getField(client_order_id)
        message.getField(side)
        message.getField(symbol)
        message.getField(price)
        message.getField(quantity)
        message.getField(order_status)
        message.getField(exec_id)

        return (symbol, price, quantity, side, client_order_id, exec_id, order_status)


def get_order_id(sender_comp_id, symbol):
    if symbol in ORDER_TABLE:
        _id = ORDER_TABLE[symbol]
    else:
        _id = 1

    order_id = sender_comp_id + symbol + str(_id)
    ORDER_TABLE[symbol] = _id + 1

    return order_id


def new_order(sender_comp_id, target_comp_id, symbol, quantity, price, side):
    curr_time = datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")
    if side.lower() == "buy":
        side = fix.Side_BUY
    else:
        side = fix.Side_SELL

    message = Message()
    header = message.getHeader()
    header.setField(fix.BeginString("FIX.4.2"))
    header.setField(fix.SenderCompID(sender_comp_id))
    header.setField(fix.TargetCompID(target_comp_id))
    header.setField(fix.MsgType("D"))
    ord_id = get_order_id(sender_comp_id, symbol)
    message.setField(fix.ClOrdID(ord_id))
    message.setField(fix.Symbol(symbol))
    message.setField(fix.Side(side))
    message.setField(fix.Price(float(price)))
    message.setField(fix.OrdType(fix.OrdType_LIMIT))
    message.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))
    message.setField(60, str(curr_time))
    message.setField(fix.OrderQty(float(quantity)))
    message.setField(fix.Text(f"{side} {symbol} {quantity}@{price}"))

    return message


def replace_order(
    sender_comp_id, target_comp_id, quantity, price, orig_client_order_id
):
    curr_time = datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")

    symbol = ORDERS[orig_client_order_id][0].getValue()
    side = ORDERS[orig_client_order_id][3].getValue()

    message = fix42.OrderCancelReplaceRequest()
    header = message.getHeader()
    header.setField(fix.SenderCompID(sender_comp_id))
    header.setField(fix.TargetCompID(target_comp_id))
    ord_id = get_order_id(sender_comp_id, symbol)
    message.setField(fix.OrigClOrdID(orig_client_order_id))
    message.setField(fix.ClOrdID(ord_id))
    message.setField(fix.Symbol(symbol))
    message.setField(fix.Side(side))
    message.setField(fix.Price(float(price)))
    message.setField(fix.OrdType(fix.OrdType_LIMIT))
    message.setField(fix.HandlInst(fix.HandlInst_MANUAL_ORDER_BEST_EXECUTION))
    message.setField(60, str(curr_time))
    message.setField(fix.OrderQty(float(quantity)))
    message.setField(fix.Text(f"{side} {symbol} {quantity}@{price}"))

    return message


def delete_order(sender_comp_id, target_comp_id, orig_client_order_id):
    curr_time = datetime.now().strftime("%Y%m%d-%H:%M:%S.%f")

    symbol = ORDERS[orig_client_order_id][0].getValue()
    side = ORDERS[orig_client_order_id][3].getValue()

    message = fix42.OrderCancelRequest()
    header = message.getHeader()
    header.setField(fix.SenderCompID(sender_comp_id))
    header.setField(fix.TargetCompID(target_comp_id))
    ord_id = get_order_id(sender_comp_id, symbol)
    message.setField(fix.OrigClOrdID(orig_client_order_id))
    message.setField(fix.ClOrdID(ord_id))
    message.setField(fix.Symbol(symbol))
    message.setField(fix.Side(side))
    # message.setField(60, str(curr_time))
    message.setField(fix.TransactTime())
    message.setField(fix.Text(f"Delete {orig_client_order_id}"))

    return message


def send(message):
    try:
        fix.Session.sendToTarget(message)
    except fix.SessionNotFound as error:
        raise logger.error(f"No session found {message}, exiting...")


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    options_metavar="[options...]",
)
@click.argument(
    "client_config", type=click.Path(exists=True), metavar="[client config]"
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Print debug messages.",
)
def main(client_config="configs/client1.cfg", debug=None):
    """FIX client

    Sends new order over a FIX session.

    """
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.info(f"Logging set to debug.")
    else:
        logger.setLevel(logging.INFO)
        logger.info(f"Logging set to info.")

    config = configparser.ConfigParser()

    config.read(client_config)

    sender_compid = config["SESSION"]["SenderCompID"]
    target_compid = config["SESSION"]["TargetCompID"]

    settings = fix.SessionSettings(client_config)
    store = fix.FileStoreFactory(settings)
    app = Client()

    app.set_logging(logger)

    initiator = fix.SocketInitiator(app, store, settings)

    initiator.start()

    sleep(1)

    while True:
        try:
            sleep(1)
            choice = int(input("Enter choice :- \n1. New order\n2. Replace order\n3. Delete order\n> "))
            if choice == 1:
                print("Enter order :- ")
                symbol = input("Symbol: ")
                price = input("Price: ")
                quantity = input("Quantity: ")
                side = input("Side: ")

                message = new_order(
                    sender_compid, target_compid, symbol, quantity, price, side
                )

                print("Sending new order...")
                send(message)
            elif choice == 2:
                order_id = input("Enter OrderID: ")
                price = input("Price: ")
                quantity = input("Quantity: ")

                message = replace_order(
                    sender_compid, target_compid, quantity, price, order_id
                )

                print("Sending replace order...")
                send(message)
            elif choice == 3:
                order_id = input("Enter OrderID: ")

                message = delete_order(
                    sender_compid, target_compid, order_id
                )

                print("Sending delete order...")
                send(message)

        except KeyboardInterrupt:
            initiator.stop()
            print("Goodbye... !\n")


if __name__ == "__main__":
    logger = setup_logging("logs/", "client")
    main()
