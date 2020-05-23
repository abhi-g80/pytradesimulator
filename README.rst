Python exchange simulator
#########################

A python based trading exchange running on FIX.4.2.

The exchange performs order matching based on FIFO order matching algorithm. Amending existing order is also supported via FIX :code:`OrderCancelReplaceRequest` message.


Order types
===========

.. code-block:: bash

    Limit
    Market


Run
===

Running ordering client and exchange server.

.. code-block:: bash

    $ ./server.py
    $ ./client.py configs/client1.cfg


Running market data client and market data adapter.

.. code-block:: bash

    $ ./market_client.py configs/mdclient1.cfg
    $ ./market_data.py


Example
=======

Start market data client.

.. code-block:: bash

    $ ./market_data.py
    2020-05-23 18:31:52.701728 [INFO   ] (main     ) Logging set to info.
    2020-05-23 18:31:52.711440 [INFO   ] (onCreate ) Successfully created sessions FIX.4.2:MARKET->MDCLIENT1.
    2020-05-23 18:31:52.716357 [INFO   ] (onCreate ) Successfully created sessions FIX.4.2:MARKET->MDCLIENT2.
    2020-05-23 18:31:52.717506 [INFO   ] (main     ) FIX.4.2 maarket data server started.
    2020-05-23 18:32:12.909809 [INFO   ] (onLogon  ) FIX.4.2:MARKET->MDCLIENT1 successfully logged in.
    2020-05-23 18:32:34.697594 [INFO   ] (onLogon  ) FIX.4.2:MARKET->MDCLIENT2 successfully logged in.

Start the market data clients and subscribe to instruments (example, MSFT, HYG).

.. code-block:: bash

    $ ./market_client.py configs/mdclient1.cfg -d
    2020-05-23 18:32:12.901025 [INFO   ] (main     ) Logging set to debug.
    2020-05-23 18:32:12.907327 [INFO   ] (onCreate ) Successfully created session FIX.4.2:MDCLIENT1->MARKET.
    2020-05-23 18:32:12.909923 [INFO   ] (onLogon  ) FIX.4.2:MDCLIENT1->MARKET session successfully logged in.
    Enter symbol to subscribe: MSFT
    2020-05-23 18:32:38.002055 [DEBUG  ] (toApp    ) Sending 8=FIX.4.29=12935=V34=249=MDCLIENT152=20200523-16:32:38.00000056=MARKET146=155=MSFT262=TESTREQUEST1263=1264=10267=3269=0269=1269=210=218 session FIX.4.2:MDCLIENT1->MARKET

Start the exchange server.

.. code-block:: bash

    $ ./server.py
    2020-05-23 18:31:57.270028 [INFO   ] (main     ) Logging set to info.
    2020-05-23 18:31:57.276828 [INFO   ] (onCreate ) Successfully created session FIX.4.2:EXCHANGE->CLIENT1.
    2020-05-23 18:31:57.280955 [INFO   ] (onCreate ) Successfully created session FIX.4.2:EXCHANGE->CLIENT2.
    2020-05-23 18:31:57.281989 [INFO   ] (main     ) FIX.4.2 server started.
    2020-05-23 18:31:57.284128 [INFO   ] (main     ) Started market data publisher at port 9000.

Start the trading clients.

.. code-block:: bash

    $ ./client.py configs/client1.cfg
    2020-05-23 18:32:48.812824 [INFO   ] (main     ) Logging set to info.
    2020-05-23 18:32:48.820117 [INFO   ] (onCreate ) Successfully created session FIX.4.2:CLIENT1->EXCHANGE.
    2020-05-23 18:32:48.821577 [INFO   ] (onLogon  ) FIX.4.2:CLIENT1->EXCHANGE session successfully logged in.
    Enter choice :-
    1. New order
    2. Replace order
    3. Delete order
    >

To send a order in MSFT, select new order and then set the required prices.

.. code-block:: bash

    Enter order :-
    Symbol: MSFT
    Price: 189
    Quantity: 675
    Side: buy
    Type: limit
    Sending new order...
    2020-05-23 18:33:27.082369 [INFO   ] (fromApp  ) Got message 8=FIX.4.29=18035=834=349=EXCHANGE52=20200523-16:33:27.00000056=CLIENT16=18911=CLIENT1MSFT114=67517=MSFT_E_00000120=031=18932=67537=MSFT_O_00000138=67539=054=155=MSFT150=0151=010=111 for FIX.4.2:CLIENT1->EXCHANGE.
    2020-05-23 18:33:27.082713 [INFO   ] (process  ) Order placed successfully.
    2020-05-23 18:33:27.082950 [INFO   ] (process  ) Order: 17=MSFT_E_000001, 11=CLIENT1MSFT1 55=MSFT 32=675@31=189 54=1

Price published to market data client.

.. code-block:: bash

    2020-05-23 18:33:27.560618 [INFO   ] (fromApp  ) Got message 8=FIX.4.29=9735=W34=449=MARKET52=20200523-16:33:27.00000056=MDCLIENT155=MSFT268=1269=0270=189271=67510=192 for FIX.4.2:MDCLIENT1->MARKET.
    8=FIX.4.2|9=97|35=W|34=4|49=MARKET|52=20200523-16:33:27.000000|56=MDCLIENT1|55=MSFT|268=1|269=0|270=189|271=675|10=192|
    Symbol: MSFT
    +------------------+--------------------+
    | bid_prc, bid_qty |  ask_prc, ask_qty  |
    +------------------+--------------------+
    |  (189.0, 675.0)  | ('Empty', 'Empty') |
    +------------------+--------------------+

Trades done will be published to the clients and to the market data subscribers.


Test
====
All tests should pass.

.. code-block:: bash

    $ py.test tests -v
