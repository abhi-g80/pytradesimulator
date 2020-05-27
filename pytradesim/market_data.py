#!/usr/bin/env python
import logging
from multiprocessing.connection import Listener

import click
import quickfix as fix
from modules.market.mda import MarketDataAdapter
from modules.market.utils import Book
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
    """FIX price gateway

    Sends market data snapshot over FIX.

    """
    if debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Logging set to debug.")
    else:
        logger.setLevel(logging.INFO)
        logger.info("Logging set to info.")

    settings = fix.SessionSettings("configs/price.cfg")
    log = fix.FileLogFactory(settings)
    store = fix.FileStoreFactory(settings)
    app = MarketDataAdapter()
    address = ("localhost", port)

    book = Book("Market", [(1, 1)], [(1, 1)], [])

    app.set_logging(logger)

    acceptor = fix.SocketAcceptor(app, store, settings, log)

    try:
        acceptor.start()

        logger.info("FIX.4.2 maarket data server started.")
        logger.debug(f"Starting listener on port {port}.")

        conn = Listener(address, authkey=b"Dj$0.Jkx1@").accept()

        logger.debug(f"Accepted orderbook connection on port {port}.")

        while True:
            book = conn.recv()
            app.dispatch(book)

    except (fix.ConfigError, fix.RuntimeError) as error:
        raise fix.RuntimeError(error)
    except KeyboardInterrupt:
        logger.info(f"Got signal interrupt, exiting...")
        acceptor.stop()


if __name__ == "__main__":
    logger = setup_logging("logs/", "marketdata")
    main()
