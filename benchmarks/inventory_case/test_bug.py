
from benchmarks.inventory_case.inventory import reconcile_inventory


def test_repeated_deductions():
    result = reconcile_inventory(
        {"widget": 10},
        [("widget", -3), ("widget", -2)]
    )
    assert result == {"widget": 5}


def test_repeated_additions_new_sku():
    result = reconcile_inventory(
        {"widget": 2},
        [("gadget", 4), ("gadget", 3)]
    )
    assert result == {"widget": 2, "gadget": 7}
