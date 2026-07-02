from acmonitor.retailers.generic import extract_price


def test_extract_simple_price() -> None:
    assert extract_price("Only £399.99 today") == 399.99


def test_extract_price_with_comma() -> None:
    assert extract_price("Price £1,249.00") == 1249.00


def test_extract_lowest_price() -> None:
    assert extract_price("Was £499.99; now only £429.99") == 429.99


def test_extract_whole_pound_price() -> None:
    assert extract_price("Now £399") == 399.0


def test_no_price() -> None:
    assert extract_price("Out of stock") is None
