Python exchange simulator
#########################

A python based trading exchange running on FIX.4.2.

The exchange performs order matching based on FIFO order matching algorithm.


Order types
===========

.. code-block:: bash

    Limit
    Market


Run
===

Running ordering client and exchange server.

.. code-block:: bash

    $ ./server.py configs/exchange.cfg
    $ ./client.py configs/client1.cfg


Running market data client and market data adapter.

.. code-block:: bash

    $ ./market_client.py configs/mdclient1.cfg
    $ ./market_data.py configs/price.cfg


Test
====
All tests should pass.

.. code-block:: bash

    $ py.test tests -v
