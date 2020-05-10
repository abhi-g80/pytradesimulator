class Instrument:
    def __init__(self, symbol, book_id, isin, reference_price, ticksize):
        self.symbol = symbol
        self.book_id = book_id
        self.isin = isin
        self.reference_price = reference_price
        self.ticksize = ticksize

    @property
    def book_id(self):
        return self._book_id

    @property
    def reference_price(self):
        return self._reference_price

    @book_id.setter
    def book_id(self, value):
        if isinstance(value, int):
            self._book_id = value
            return self._book_id
        else:
            raise ValueError(
                f"Incorrect type {type(value)} for book identifier, must be integer."
            )

    @reference_price.setter
    def reference_price(self, value):
        if isinstance(value, float):
            self._reference_price = value
            return self._reference_price
        else:
            raise ValueError(
                f"Incorrect type {type(value)} for reference price, must be float."
            )

    def __repr__(self):
        return (
            f"Instrument(symbol={self.symbol}, book_id={self.book_id}, "
            f"reference_price={self.reference_price}, "
            f"isin={self.isin}, ticksize={self.ticksize})"
        )
