from pytradesim.modules.orderbook import Order, Orderbook, Side, Trade


def test_orderbook_limit_order():
    order = Order("HYG", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")

    assert order.symbol == "HYG"
    assert order.price == 23.54
    assert order.quantity == 100
    assert order.side == Side.BID
    assert order.order_type == "LIMIT"
    assert order.order_id == "NEWORDER_1"
    assert order.session == "TESTSESSION"


def test_orderbook_market_order():
    order = Order("HYG", 23.54, 100, 1, 1, "NEWORDER_1", "TESTSESSION")

    assert order.symbol == "HYG"
    assert order.price == 23.54
    assert order.quantity == 100
    assert order.side == Side.BID
    assert order.order_type == "MARKET"
    assert order.order_id == "NEWORDER_1"
    assert order.session == "TESTSESSION"


def test_orderbook_trade():
    trade = Trade("HYG", 100, 23.54, 1, "NEWTRADE_1", "HYG1", "TESTSESSION")

    assert trade.symbol == "HYG"
    assert trade.price == 23.54
    assert trade.quantity == 100
    assert trade.side == Side.BID
    assert trade.exec_id == "NEWTRADE_1"
    assert trade.order_id == "HYG1"
    assert trade.session == "TESTSESSION"


def test_orderbook_symbol():
    orderbook = Orderbook("TEST")

    assert orderbook.symbol == "TEST"


def test_orderbook_reject():
    order = Order("HYG", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")

    orderbook = Orderbook("TEST")

    assert orderbook.new_order(order) == "[Internal] incorrect orderbook assignment"


def test_orderbook_insertion():
    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.new_order(order)

    inserted_order = orderbook.bids[23.54][0]

    assert inserted_order.symbol == "TEST"
    assert inserted_order.price == 23.54
    assert inserted_order.quantity == 100
    assert inserted_order.side == Side.BID
    assert inserted_order.order_id == "NEWORDER_1"


def test_orderbook_deletion():
    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.new_order(order)

    orderbook.delete_order("NEWORDER_1")

    assert len(orderbook.bids[23.54]) == 0


def test_orderbook_replace_size():
    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.new_order(order)

    print(orderbook._show_orderbook())

    order = Order("TEST", 23.54, 120, 1, 2, "NEWORDER_2", "TESTSESSION")

    orderbook.replace_order("NEWORDER_1", order)

    print(orderbook._show_orderbook())

    assert orderbook.bids[23.54][0].quantity == 120


def test_orderbook_replace_price_and_size():
    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook = Orderbook("TEST")

    orderbook.new_order(order)

    order = Order("TEST", 23.55, 120, 1, 2, "NEWORDER_2", "TESTSESSION")

    orderbook.replace_order("NEWORDER_1", order)

    assert orderbook.bids[23.55][0].quantity == 120
    assert orderbook.bids[23.55][0].price == 23.55


def test_orderbook_full_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.54, 100, 2, 2, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 100
        assert trade.exec_id == "TEST_TEST000001"


def test_orderbook_market_order_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.59, 50, 2, 1, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

    assert orderbook.trades.qsize() == 2

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 50
        assert trade.exec_id == "TEST_TEST000001"

    assert orderbook.bids[23.54][0].quantity == 50


def test_orderbook_market_order_no_match():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.52, 50, 1, 1, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

    assert orderbook.trades.qsize() == 0
    assert orderbook.bids[23.54][0].quantity == 100
    assert orderbook.bbo() == (23.54, float("inf"))


def test_orderbook_partial_passive_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 100, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.54, 50, 2, 2, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.54
        assert trade.quantity == 50
        assert trade.exec_id == "TEST_TEST000001"

    assert orderbook.bids[23.54][0].quantity == 50


def test_orderbook_partial_aggressive_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 50, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.54, 100, 2, 2, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

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

    order = Order("TEST", 23.54, 50, 1, 2, "NEWORDER_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.54, 30, 1, 2, "NEWORDER_2", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.53, 10, 1, 2, "NEWORDER_3", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.53, 20, 1, 2, "NEWORDER_3_1", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.51, 10, 1, 2, "NEWORDER_4", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.55, 100, 2, 2, "NEWORDER_5", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.56, 30, 2, 2, "NEWORDER_6", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.58, 80, 2, 2, "NEWORDER_7", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.60, 90, 2, 2, "NEWORDER_8", "TESTSESSION")
    orderbook.new_order(order)

    order = Order("TEST", 23.53, 150, 2, 2, "NEWORDER_9", "TESTSESSION")
    orderbook.new_order(order)

    assert orderbook.trades.qsize() == 8

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        if trade.price == 23.54:
            assert trade.quantity in [50, 30]
            if trade.quantity == 50 and trade.side == Side.BID:
                assert trade.order_id == "NEWORDER_1"
            elif trade.quantity == 30 and trade.side == Side.BID:
                assert trade.order_id == "NEWORDER_2"
            elif trade.side == Side.OFFER:
                assert trade.order_id == "NEWORDER_9"

        if trade.price == 23.53:
            assert trade.quantity in [10, 20]

    assert orderbook.best_ask == 23.53
    assert orderbook.best_bid == 23.51
    assert orderbook.asks[23.53][0].order_id == "NEWORDER_9"


def test_orderbook_bbo():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 150, 1, 2, "TESTSESSION_1_NEWORDER_1", "TESTSESSION_1")
    orderbook.new_order(order)

    order = Order("TEST", 23.55, 130, 2, 2, "TESTSESSION_2_NEWORDER_1", "TESTSESSION_2")
    orderbook.new_order(order)

    assert orderbook.bbo() == (23.54, 23.55)


def test_orderbook_replace_execution():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 150, 1, 2, "TESTSESSION_1_NEWORDER_1", "TESTSESSION_1")
    orderbook.new_order(order)

    order = Order("TEST", 23.55, 130, 2, 2, "TESTSESSION_2_NEWORDER_1", "TESTSESSION_2")
    orderbook.new_order(order)

    order = Order("TEST", 23.55, 140, 1, 2, "TESTSESSION_1_NEWORDER_2", "TESTSESSION_1")
    orderbook.replace_order("TESTSESSION_1_NEWORDER_1", order)

    assert orderbook.trades.qsize() == 2

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.55
        assert trade.quantity == 130

    assert orderbook.bbo() == (23.55, float("inf"))


def test_orderbook_deletion_bbo():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 150, 1, 2, "TESTSESSION_1_NEWORDER_1", "TESTSESSION_1")
    orderbook.new_order(order)

    order = Order("TEST", 23.55, 130, 2, 2, "TESTSESSION_2_NEWORDER_1", "TESTSESSION_2")
    orderbook.new_order(order)

    order = Order("TEST", 23.56, 120, 2, 2, "TESTSESSION_2_NEWORDER_2", "TESTSESSION_2")
    orderbook.new_order(order)

    assert orderbook.bbo() == (23.54, 23.55)

    assert len(orderbook.asks[23.55]) == 1

    orderbook.delete_order("TESTSESSION_2_NEWORDER_1")

    assert len(orderbook.asks[23.55]) == 0

    assert orderbook.bbo() == (23.54, 23.56)


def test_orderbook_replace_execution_deletion():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.54, 150, 1, 2, "TESTSESSION_1_NEWORDER_1", "TESTSESSION_1")
    orderbook.new_order(order)

    order = Order("TEST", 23.54, 250, 1, 2, "TESTSESSION_3_NEWORDER_1", "TESTSESSION_3")
    orderbook.new_order(order)

    order = Order("TEST", 23.57, 130, 2, 2, "TESTSESSION_2_NEWORDER_1", "TESTSESSION_2")
    orderbook.new_order(order)

    order = Order("TEST", 23.59, 120, 2, 2, "TESTSESSION_2_NEWORDER_2", "TESTSESSION_2")
    orderbook.new_order(order)

    assert orderbook.bbo() == (23.54, 23.57)

    order = Order("TEST", 23.56, 350, 1, 2, "TESTSESSION_3_NEWORDER_2", "TESTSESSION_3")
    orderbook.replace_order("TESTSESSION_3_NEWORDER_1", order)

    assert orderbook.bbo() == (23.56, 23.57)
    # orderbook.delete_order("TESTSESSION_2_NEWORDER_1")

    order = Order("TEST", 23.56, 351, 2, 2, "TESTSESSION_2_NEWORDER_3", "TESTSESSION_2")
    orderbook.replace_order("TESTSESSION_2_NEWORDER_2", order)

    assert orderbook.trades.qsize() == 2

    assert orderbook.bbo() == (23.54, 23.56)

    while not orderbook.trades.empty():
        trade = orderbook.trades.get()

        assert trade.price == 23.56
        assert trade.quantity == 350

    orderbook.delete_order("TESTSESSION_2_NEWORDER_3")

    assert orderbook.bbo() == (23.54, 23.57)


def test_orderbook_duplicate_order_id():
    orderbook = Orderbook("TEST")

    order = Order("TEST", 23.59, 120, 2, 2, "TESTSESSION_2_NEWORDER_2", "TESTSESSION_2")
    orderbook.new_order(order)

    order = Order("TEST", 23.49, 130, 1, 2, "TESTSESSION_2_NEWORDER_2", "TESTSESSION_2")

    assert orderbook.new_order(order) == "[Internal] duplicate order ID received"
