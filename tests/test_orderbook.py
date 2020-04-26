import pytest
import sys

from pytradesim.orderbook import Orderbook, Order, Trade


def test_order():
    order = Order("HYG", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")

    assert order.symbol == "HYG"
    assert order.price == 23.54
    assert order.quantity == 100
    assert order.side == "b"
    assert order.order_id == "NEWORDER_1"
    assert order.session == "TESTSESSION"


def test_trade():
    trade = Trade("HYG", 100, 23.54, "b", "NEWTRADE_1", "HYG1", "TESTSESSION")

    assert trade.symbol == "HYG"
    assert trade.price == 23.54
    assert trade.quantity == 100
    assert trade.side == "b"
    assert trade.exec_id == "NEWTRADE_1"
    assert trade.order_id == "HYG1"
    assert trade.session == "TESTSESSION"


def test_orderbook_symbol():
    orderbook = Orderbook("TEST")

    assert orderbook.symbol == "TEST"


def test_orderbook_reject():
    order = Order("HYG", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")

    orderbook = Orderbook("TEST")

    assert orderbook.process_incoming_order(order) == "Incorrect orderbook assignment"


def test_orderbook_insertion():
    order = Order("TEST", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.process_incoming_order(order)

    inserted_order = orderbook.bids[23.54][0]

    assert inserted_order.symbol == "TEST"
    assert inserted_order.price == 23.54
    assert inserted_order.quantity == 100
    assert inserted_order.side == "b"
    assert inserted_order.order_id == "NEWORDER_1"


def test_orderbook_deletion():
    order = Order("TEST", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.process_incoming_order(order)

    orderbook._delete_order(order)

    assert len(orderbook.bids[23.54]) == 0


def test_orderbook_replace():
    order = Order("TEST", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.54, 120, "B", "NEWORDER_1", "TESTSESSION")

    orderbook._replace_order(order)

    assert orderbook.bids[23.54][0].quantity == 120


def test_orderbook_full_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.54, 100, "S", "NEWORDER_2", "TESTSESSION")
    orderbook.process_incoming_order(order)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 100
        assert trade.exec_id == "TEST_TEST000001"


def test_orderbook_partial_passive_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, "B", "NEWORDER_1", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.54, 50, "S", "NEWORDER_2", "TESTSESSION")
    orderbook.process_incoming_order(order)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 50
        assert trade.exec_id == "TEST_TEST000001"
    
    assert orderbook.bids[23.54][0].quantity == 50


def test_orderbook_partial_aggressive_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 50, "B", "NEWORDER_1", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.54, 100, "S", "NEWORDER_2", "TESTSESSION")
    orderbook.process_incoming_order(order)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 50
        assert trade.exec_id == "TEST_TEST000001"
    
    assert orderbook.asks[23.54][0].quantity == 50
    assert orderbook.asks[23.54][0].order_id == "NEWORDER_2"
    assert len(orderbook.bids[23.54]) == 0


def test_orderbook_multiple_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 50, "B", "NEWORDER_1", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.54, 30, "B", "NEWORDER_2", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.53, 10, "B", "NEWORDER_3", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.53, 20, "B", "NEWORDER_3_1", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.51, 10, "B", "NEWORDER_4", "TESTSESSION")
    orderbook.process_incoming_order(order)


    order = Order("TEST", 23.55, 100, "S", "NEWORDER_5", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.56, 30, "S", "NEWORDER_6", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.58, 80, "S", "NEWORDER_7", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.60, 90, "S", "NEWORDER_8", "TESTSESSION")
    orderbook.process_incoming_order(order)

    order = Order("TEST", 23.53, 150, "S", "NEWORDER_9", "TESTSESSION")
    orderbook.process_incoming_order(order)

    assert orderbook.trades.qsize() == 8

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        if trade.price == 23.54:
            assert trade.quantity in [50, 30]
            if trade.quantity == 50 and trade.side == "b":
                assert trade.order_id == "NEWORDER_1"
            elif trade.quantity == 30 and trade.side == "b":
                assert trade.order_id == "NEWORDER_2"
            elif trade.side == "s":
                assert trade.order_id == "NEWORDER_9"

        if trade.price == 23.53:
            assert trade.quantity in [10, 20]

    assert orderbook.best_ask == 23.53
    assert orderbook.best_bid == 23.51
    assert orderbook.asks[23.53][0].order_id == "NEWORDER_9"
