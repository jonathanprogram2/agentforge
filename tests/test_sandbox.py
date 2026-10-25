
import pytest

from app.sandbox import validate_patch


@pytest.mark.parametrize(
    "benchmark, code",
    [
        (
            "pricing_case",
            "def discounted_price(price, discount_pct):\n"
            "    return price\n",
        ),
        (
            "inventory_case",
            "def reconcile_inventory(stock, movements):\n"
            "    return stock\n",
        ),
    ],
)
def test_valid_patches(benchmark, code):
    validate_patch(benchmark, code)


@pytest.mark.parametrize(
    "code",
    [
        "def wrong_function():\n    pass\n",
        "import os\n"
        "def discounted_price(price, discount_pct):\n"
        "    return price\n",
        "def discounted_price(price, discount_pct):\n"
        "    return price\n"
        "def helper():\n    return 0\n",
        "def discounted_price(:\n    pass\n",
    ],
)
def test_invalid_patches_are_rejected(code):
    with pytest.raises(ValueError):
        validate_patch("pricing_case", code)


@pytest.mark.parametrize(
    "body",
    [
        "    import os\n    return price\n",
        '    open("secret.txt")\n    return price\n',
        '    exec("print(1)")\n    return price\n',
        "    return globals()\n",
        "    return price.__class__\n",
    ],
)
def test_restricted_operations_are_rejected(body):
    code = (
        "def discounted_price(price, discount_pct):\n"
        + body
    )

    with pytest.raises(ValueError):
        validate_patch("pricing_case", code)
