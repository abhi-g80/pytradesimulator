#!/usr/bin/env python

import configparser
import logging
import sys
from time import sleep

import click
import quickfix as fix
from modules.market.client import MarketDataClient
from modules.utils import setup_logging


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
def main(client_config="configs/mdclient1.cfg", debug=None):
    """FIX market data client

    Client to receive market data over a FIX session.

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
    app = MarketDataClient()

    app.set_logging(logger)

    initiator = fix.SocketInitiator(app, store, settings)

    initiator.start()

    sleep(1)

    symbol = input("Enter symbol to subscribe: ")

    app.market_data_request(sender_compid, target_compid, [symbol])

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        logger.info("Caught interrupt, exiting...")
        initiator.stop()
        sys.exit()


if __name__ == "__main__":
    logger = setup_logging("logs/", "client")
    main()
