#!/usr/bin/env python

import logging

from datetime import datetime
from time import sleep

from modules.orderbook import Orderbook, Order, Trade
from modules.broker import MessageBroker, MARKETS
from modules.utils import LogFormat, setup_logging, Message

import click
import quickfix as fix


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    options_metavar="[options...]",
)
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Print debug messages.",
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
