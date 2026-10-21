

from benchmarks.pricing_case.pricing import discounted_price

def test_ten_percent_discount():
    assert discounted_price(100.0, 10) == 90.0

def test_fifty_percent_discount():
    assert discounted_price(80.0, 50) == 40.0