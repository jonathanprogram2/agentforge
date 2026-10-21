
def discounted_price(price: float, discount_pct: float) -> float:
    return round(price * (1 + discount_pct / 100), 2)