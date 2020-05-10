from pytradesim.modules.instrument import Instrument


def test_instrument_new():
    instrument = Instrument("HYG", 101, "ISIN000101", 78.95, 0.01)

    assert instrument.symbol == "HYG"
    assert instrument.book_id == 101
    assert instrument.isin == "ISIN000101"
    assert instrument.reference_price == 78.95
    assert instrument.ticksize == 0.01
