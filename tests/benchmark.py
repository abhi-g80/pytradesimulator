import random
import sys
from statistics import mean, median
from time import time

import click
from pytradesim.modules.orderbook import Order, Orderbook

sys.path.append("..")


class Timer:
    def __enter__(self):
        self.__start = time()
        return self

    def __exit__(self, *args):
        self.time = time() - self.__start


def generate(sample_size):
    orders = []
    session = "TESTSESSION"

    for i in range(sample_size):
        price = round(random.uniform(0, 50), 2)
        quantity = random.randint(1, sample_size)
        side = random.choice(["B", "S"])
        order_id = session + "_" + str(i)
        orders.append(Order("TEST", price, quantity, side, 2, order_id, session))

    return orders


def stats(array: list):
    print(f"Count - {len(array)}")
    print(f"Mean - {mean(array) * 1e6:.3f} µs")
    print(f"Median - {median(array) * 1e6:.3f} µs")
    print(f"Max - {max(array) * 1e6:.3f} µs")
    print(f"Min - {min(array) * 1e6:.3f} µs")
    print()


def run(size: int, prob: float) -> None:
    with Timer() as timer:
        orders = generate(size)
    click.secho(f"Generated {size} orders in {timer.time * 1e6:.3f} µs", fg="cyan")
    print()

    # for order in orders:
    #     print(order)

    orderbook = Orderbook("TEST")

    order_add_stats = []
    order_delete_stats = []
    live_orders = []

    while orders:
        if random.uniform(0, 1) < prob:
            order = random.choice(orders)
            with Timer() as timer:
                orderbook.new_order(order)
            order_add_stats.append(timer.time)
            live_orders.append(order.order_id)
            orders.remove(order)
        else:
            if live_orders:
                order_id = random.choice(live_orders)
                with Timer() as timer:
                    orderbook.delete_order(order_id)
                order_delete_stats.append(timer.time)
                live_orders.remove(order_id)

    if order_add_stats:
        click.secho("Order add stats:-", fg="green")
        stats(order_add_stats)

    if order_delete_stats:
        click.secho("Order delete stats:-", fg="green")
        stats(order_delete_stats)


@click.command(options_metavar="[options]")
@click.option(
    "--probability", "-p", default=0.5, show_default=True, help="Order add probability."
)
@click.option(
    "--sample-size", "-s", default=5000, show_default=True, help="No.of orders."
)
def main(sample_size: int, probability: float):
    run(sample_size, probability)


if __name__ == "__main__":
    main()
