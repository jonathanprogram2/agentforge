

from benchmarks.pricing_case.pricing import discounted_price

def test_zero_discount():
    assert discounted_price(100.0, 0) == 100.0

def test_zero_price():
    assert discounted_price(0.0, 20) == 0.0