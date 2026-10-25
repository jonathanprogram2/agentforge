
from benchmarks.inventory_case.inventory import reconcile_inventory


def test_interleaved_updates():
    result = reconcile_inventory(
        {"widget": 4},
        [
            ("widget", -3),
            ("widget", 5),
            ("widget", -2),
        ],
    )

    assert result == {"widget": 4}


def test_clamp_then_restock():
    result = reconcile_inventory(
        {"widget": 3},
        [
            ("widget", -10),
            ("widget", 4),
        ],
    )

    assert result == {"widget": 4}


def test_multiple_sku_movements():
    result = reconcile_inventory(
        {"a": 5, "b": 2},
        [
            ("a", -2),
            ("b", 3),
            ("a", -1),
            ("c", 2),
        ],
    )

    assert result == {
        "a": 2,
        "b": 5,
        "c": 2,
    }


def test_no_movements():
    original = {"widget": 8}

    result = reconcile_inventory(original, [])

    assert result == {"widget": 8}
    assert original == {"widget": 8}
