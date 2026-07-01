from acmonitor.retailers.generic import extract_price


def test_extract_simple_price():
    assert extract_price("Only £399.99 today") == 399.99


def test_extract_price_with_comma():
    assert extract_price("Price £1,249.00") == 1249.00


def test_extract_lowest_price():
    text = """
    Was £499.99
    Now only £429.99
    """

    assert extract_price(text) == 429.99


def test_no_price():
    assert extract_price("Out of stock") is None
