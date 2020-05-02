Python trade simulator engine
#############################

A simulation exchange to perform add limit orders and get execution over FIX4.2.

A client, a server and a limit orderbook engine matching orders. The client connects
over a FIX4.2 session to server (a.k.a broker). The broker then sends the incoming
order to orderbook.


Test
====
All tests should pass.

    $ py.test tests -v
