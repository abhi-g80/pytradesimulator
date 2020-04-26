#!/usr/bin/env python

import logging

from datetime import datetime
from time import sleep

from orderbook import Orderbook, Order, Trade
from broker import MessageBroker, MARKETS

import click
import quickfix as fix


class LogFormat(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        log_time = datetime.fromtimestamp(record.created)
        microseconds = "{0:.6f}".format(record.created).rsplit(".")[1]
        formatted_logline = f"{log_time.strftime('%Y-%m-%d %H:%M:%S')}.{microseconds}"

        return formatted_logline

    def format(self, record):
        indent = "\n    "
        msg = logging.Formatter.format(self, record)

        return indent.join([line for line in msg.split("\n")])


def setup_logging(log_path, file_name):
    log_formatter = LogFormat(fmt="%(asctime)s [%(levelname)-7.7s] (%(funcName)-9.9s) %(message)s")
    root_logger = logging.getLogger()

    file_handler = logging.FileHandler("{0}/{1}.log".format(log_path, file_name))
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    return root_logger


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    options_metavar="[options...]",
)
@click.option(
        "-d", "--debug", is_flag=True, default=False,
        show_default=True, help="Print debug messages."
)
def main(debug=None):
    """FIX gateway

    Accepts orders over a FIX session.

    """
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.info(f"Logging set to debug.")
    else:
        logger.setLevel(logging.INFO)
        logger.info(f"Logging set to info.")

    settings = fix.SessionSettings("configs/exchange.cfg")
    log = fix.FileLogFactory(settings)
    store = fix.FileStoreFactory(settings)
    app = MessageBroker()

    app.set_logging(logger)

    acceptor = fix.SocketAcceptor(app, store, settings, log)

    try:
        acceptor.start()
        logger.info("FIX4.2 server started.")

        while True:
            sleep(1)
            if MARKETS:
                for market in MARKETS:
                    logger.debug(f"\n{MARKETS[market]._show_orderbook()}")

    except (fix.ConfigError, fix.RuntimeError) as error:
        raise fix.RuntimeError(error)
    except KeyboardInterrupt:
        logger.info(f"Got signal interrupt, exiting...")
        acceptor.stop()


if __name__ == "__main__":
    logger = setup_logging("logs/", "server")
    main()
