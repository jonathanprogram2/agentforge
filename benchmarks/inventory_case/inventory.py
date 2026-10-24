
def reconcile_inventory(
    stock: dict[str, int],
    movements: list[tuple[str, int]]
) -> dict[str, int]:
    """
    Apply inventory movements sequentially.

    Each movement changes an item's quantity.
    Quantities cannot fall below zero.
    The original stock dictionary must remain unchanged.
    """
    updated = stock.copy()

    for sku, delta in movements:
        current = stock.get(sku, 0)
        updated[sku] = max(0, current + delta)

    return updated
