import queue
import time
from collections import defaultdict
from enum import Enum

from prettytable import PrettyTable


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2


class Orderbook:
    def __init__(self, symbol):
        self.symbol = symbol
        self._id = 0
        self.trades = queue.Queue()
        self.bids = defaultdict(list)
        self.asks = defaultdict(list)
        self.live_order_ids = {}

    @property
    def best_bid(self):
        if self.bids:
            return max([k for k in self.bids if self.bids[k]], default=float("-inf"))
        else:
            return float("-inf")

    @property
    def best_ask(self):
        if self.asks:
            return min([k for k in self.asks if self.asks[k]], default=float("inf"))
        else:
            return float("inf")

    def bbo(self):
        return (self.best_bid, self.best_ask)

    def _level_qty(self, level):
        if level:
            qty = 0
            for order in level:
                qty += order.quantity
            return qty
        else:
            return 0

    def book(self):
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

        return _bid_levels, _ask_levels

    def _show_orderbook(self):
        table = PrettyTable()

        _bid_levels, _ask_levels = self.book()

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

    def __checks(self, order):
        if order.symbol != self.symbol:
            return "[Internal] incorrect orderbook assignment"

        if order.order_id not in self.live_order_ids:
            self.live_order_ids[order.order_id] = (order.price, order.side)
        else:
            return "[Internal] duplicate order ID sent"

    def new_order(self, order):
        result = self.__checks(order)

        if result:
            return result

        # timestamp = order.timestamp
        side = order.side
        order_type = order.order_type
        best_bid, best_ask = self.best_bid, self.best_ask

        # Market
        if order_type == "MARKET":
            order.price = float("-inf") if side == "s" else float("inf")
            self.__process_execution(order)
            return

        # Limit
        if order_type == "LIMIT":
            if side == "b":
                if order.price >= best_ask and self.asks:
                    self.__process_execution(order)
                    if order.quantity > 0:
                        self.bids[order.price].append(order)
                else:
                    self.bids[order.price].append(order)
            else:
                if order.price <= best_bid and self.bids:
                    self.__process_execution(order)
                    if order.quantity > 0:
                        self.asks[order.price].append(order)
                else:
                    self.asks[order.price].append(order)

    def replace_order(self, orig_order_id, order):
        levels = self.asks if order.side == "s" else self.bids
        price = self.live_order_ids[orig_order_id][0]

        for resting_order in levels[price]:
            if resting_order.order_id == orig_order_id:
                levels[price].remove(resting_order)
                self.new_order(order)
                break

    def delete_order(self, orig_order_id):
        if orig_order_id not in self.live_order_ids:
            return "[Internal] orignal order ID not found"

        price, side = self.live_order_ids[orig_order_id]
        levels = self.asks if side == "s" else self.bids

        for resting_order in levels[price]:
            if resting_order.order_id == orig_order_id:
                levels[price].remove(resting_order)
                self.live_order_ids.pop(orig_order_id)
                break

    def __match(self, side, order_price, book_price):
        if side == "s":
            return order_price <= book_price
        else:
            return order_price >= book_price

    def __process_execution(self, order):
        levels = self.asks if order.side == "b" else self.bids

        prices = sorted(levels.keys(), reverse=(order.side == "s"))

        for price in prices:
            if order.quantity > 0 and self.__match(order.side, order.price, price):
                for resting_order in levels[price]:
                    if order.quantity == 0:
                        break

                    executions = self.__execute(order, resting_order)

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

    def __execute(self, order, resting_order):
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
    def __init__(self, symbol, price, quantity, side, order_type, order_id, session):
        self.symbol = symbol
        self.session = session
        self.price = price
        self.quantity = quantity
        self.side = side
        self.order_type = order_type
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

    @property
    def order_type(self):
        return self._order_type

    @order_type.setter
    def order_type(self, value):
        try:
            self._order_type = OrderType(value).name
            return self._order_type
        except ValueError as error:
            raise ValueError(error)

    def __repr__(self):
        return (
            f"Order(session={self.session}, symbol={self.symbol}, "
            f"price={self.price}, quantity={self.quantity}, side={self.side}, "
            f"order_type={self.order_type}, session={self.session}, "
            f"order_id={self.order_id}, timestamp={self.timestamp})"
        )
