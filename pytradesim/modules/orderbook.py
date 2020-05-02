from collections import defaultdict
import queue
import time

from prettytable import PrettyTable


class Orderbook:
    def __init__(self, symbol):
        self.symbol = symbol
        self._id = 0
        self.trades = queue.Queue()
        self.bids = defaultdict(list)
        self.asks = defaultdict(list)
        self.order_ids = {}

    @property
    def best_bid(self):
        if self.bids:
            return max(self.bids.keys())
        else:
            return float("-inf")

    @property
    def best_ask(self):
        if self.asks:
            return min(self.asks.keys())
        else:
            return float("inf")

    def _level_qty(self, level):
        if level:
            qty = 0
            for order in level:
                qty += order.quantity
            return qty
        else:
            # return "Empty"
            return 0

    def _show_orderbook(self):
        table = PrettyTable()
        bid_prices = sorted(self.bids.keys(), reverse=True)
        ask_prices = sorted(self.asks.keys())
        _bid_levels = []
        _ask_levels = []

        for bid_prc in bid_prices:
            bid_qty = self._level_qty(self.bids[bid_prc])
            if bid_qty != 0:
                _bid_levels.append((bid_prc, bid_qty))

        for ask_prc in ask_prices:
            ask_qty = self._level_qty(self.asks[ask_prc])
            if ask_qty != 0:
                _ask_levels.append((ask_prc, ask_qty))

        if len(_ask_levels) > len(_bid_levels):
            diff = len(_ask_levels) - len(_bid_levels)
            while diff:
                _bid_levels.append(("Empty", "Empty"))
                diff -= 1
        elif len(_bid_levels) > len(_ask_levels):
            diff = len(_bid_levels) - len(_ask_levels)
            while diff:
                _ask_levels.append(("Empty", "Empty"))
                diff -= 1

        table.add_column("bid_prc, bid_qty", _bid_levels)
        table.add_column("ask_prc, ask_qty", _ask_levels)

        print(f"Symbol: {self.symbol}")
        print(table)

    def process_incoming_order(self, order):
        if order.symbol != self.symbol:
            return "[Internal] Incorrect orderbook assignment"

        timestamp = order.timestamp
        side = order.side
        best_bid, best_ask = self.best_bid, self.best_ask

        if order.order_id not in self.order_ids:
            self.order_ids[order.order_id] = order.price
        else:
            return "[Internal] duplicate order ID sent"

        if side == "b":
            if order.price >= best_ask and self.asks:
                self.process_execution(order)
                if order.quantity > 0:
                    self.bids[order.price].append(order)
            else:
                self.bids[order.price].append(order)
        else:
            if order.price <= best_bid and self.bids:
                self.process_execution(order)
                if order.quantity > 0:
                    self.asks[order.price].append(order)
            else:
                self.asks[order.price].append(order)

    def _replace_order(self, orig_order_id, order):
        levels = self.asks if order.side == "s" else self.bids
        price = self.order_ids[orig_order_id]

        for resting_order in levels[price]:
            if resting_order.order_id == orig_order_id:
                levels[resting_order.price].remove(resting_order)
                if order.price in levels:
                    levels[order.price].append(order)
                else:
                    levels[order.price] = [order]
                break

    def _delete_order(self, order):
        levels = self.asks if order.side == "s" else self.bids

        for resting_order in levels[order.price]:
            if resting_order.order_id == order.order_id:
                levels[order.price].remove(resting_order)
                break

    def _match(self, side, order_price, book_price):
        if side == "s":
            return order_price <= book_price
        else:
            return order_price >= book_price

    def process_execution(self, order):
        levels = self.asks if order.side == "b" else self.bids

        prices = sorted(levels.keys(), reverse=(order.side == "s"))

        for price in prices:
            if order.quantity > 0 and self._match(order.side, order.price, price):

                for resting_order in levels[price]:
                    if order.quantity == 0:
                        break

                    executions = self.execute(order, resting_order)

                    for trade in executions:
                        self.trades.put(trade)

                for resting_order in list(levels[price]):
                    if resting_order.quantity == 0:
                        levels[price].remove(resting_order)

            if len(levels[price]) == 0:
                levels.pop(price)

    def execution_id(self):
        self._id = self._id + 1
        exec_id = "TEST_" + self.symbol + f"{self._id:06}"

        return exec_id

    def execute(self, order, resting_order):
        size = min(order.quantity, resting_order.quantity)
        order.quantity -= size
        resting_order.quantity -= size

        exec_id = self.execution_id()

        return (
            Trade(
                resting_order.symbol,
                size,
                resting_order.price,
                resting_order.side,
                exec_id,
                resting_order.order_id,
                resting_order.session,
            ),
            Trade(
                order.symbol,
                size,
                resting_order.price,
                order.side,
                exec_id,
                order.order_id,
                order.session,
            ),
        )


class MatchingEngine:
    def timestamp(self):
        return time.time() * 1e6


class Trade(MatchingEngine):
    def __init__(self, symbol, quantity, price, side, exec_id, order_id, session):
        self.symbol = symbol
        self.price = price
        self.quantity = quantity
        self.side = side
        self.exec_id = exec_id
        self.order_id = order_id
        self.session = session
        self.timestamp = self.timestamp()

    def __repr__(self):
        return (
            f"Trade(session={self.session}, symbol={self.symbol}, price={self.price}, "
            f"quantity={self.quantity}, side={self.side}, "
            f"exec_id={self.exec_id}, order_id={self.order_id}, "
            f"timestamp={self.timestamp})"
        )


class Order(MatchingEngine):
    def __init__(self, symbol, price, quantity, side, order_id, session):
        self.symbol = symbol
        self.session = session
        self.price = price
        self.quantity = quantity
        self.side = side
        self.order_id = order_id
        self.timestamp = self.timestamp()

    @property
    def side(self):
        return self._side

    @side.setter
    def side(self, value):
        if value and value.lower() in ["b", "s"]:
            self._side = value.lower()
        else:
            raise ValueError(
                "Side cannot be empty and should be 'b' (buy) or 's' (sell)."
            )

    def __repr__(self):
        return (
            f"Order(session={self.session}, symbol={self.symbol}, price={self.price}, "
            f"quantity={self.quantity}, side={self.side}, session={self.session}, "
            f"order_id={self.order_id}, timestamp={self.timestamp})"
        )
