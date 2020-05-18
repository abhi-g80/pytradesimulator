#!/usr/bin/env python

import logging
from multiprocessing.connection import Client
from time import sleep

import click
import quickfix as fix
from modules.broker import FLUSH_BOOK, MARKETS, MessageBroker
from modules.market.mda import Book
from modules.utils import setup_logging


@click.command(
    context_settings=dict(help_option_names=["-h", "--help"]),
    options_metavar="[options...]",
)
@click.option("--port", "-p", default=9000, show_default=True, help="Listening port.")
@click.option(
    "-d",
    "--debug",
    is_flag=True,
    default=False,
    show_default=True,
    help="Print debug messages.",
)
def main(port=9000, debug=None):
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
    address = ("localhost", port)

    app.set_logging(logger)

    acceptor = fix.SocketAcceptor(app, store, settings, log)

    try:
        acceptor.start()
        logger.info("FIX.4.2 server started.")

        conn = Client(address, authkey=b"Dj$0.Jkx1@")

        logger.info(f"Started market data publisher at port {port}.")

        while True:
            sleep(1)
            if MARKETS:
                for market in MARKETS:
                    logger.debug(f"\n{MARKETS[market]._show_orderbook()}")
                    if market in FLUSH_BOOK:
                        bids, asks = MARKETS[market].book()
                        trades = []
                        if FLUSH_BOOK[market]:
                            # trades
                            trades = FLUSH_BOOK[market]
                        book = Book(market, bids, asks, trades)
                        conn.send(book)
                        FLUSH_BOOK.pop(market)

    except (fix.ConfigError, fix.RuntimeError) as error:
        raise fix.RuntimeError(error)
    except KeyboardInterrupt:
        logger.info(f"Got signal interrupt, exiting...")
        acceptor.stop()


if __name__ == "__main__":
    logger = setup_logging("logs/", "server")
    main()
