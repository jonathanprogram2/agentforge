
from benchmarks.inventory_case.inventory import reconcile_inventory


def test_single_adjustment():
    result = reconcile_inventory(
        {"widget": 10},
        [("widget", -3)]
    )
    assert result == {"widget": 7}


def test_floor_zero():
    result = reconcile_inventory(
        {"widget": 2},
        [("widget", -7)]
    )
    assert result == {"widget": 0}


def test_original_unchanged():
    original = {"widget": 10}

    result = reconcile_inventory(
        original,
        [("widget", 2)]
    )

    assert original == {"widget": 10}
    assert result == {"widget": 12}
