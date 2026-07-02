from acmonitor.retailers.generic import _availability_from_jsonld, _price_from_jsonld


def test_jsonld_multiple_offers_uses_available_offer_and_lowest_price() -> None:
    product = {
        "offers": [
            {"availability": "https://schema.org/OutOfStock", "price": "499.99"},
            {"availability": "https://schema.org/InStock", "price": "429.99"},
        ]
    }
    assert _availability_from_jsonld(product)[0] is True
    assert _price_from_jsonld(product) == 429.99
