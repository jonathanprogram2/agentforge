

from benchmarks.pagination_case.pagination import paginate

def test_first_page():
    result = paginate([1, 2, 3, 4, 5], 1, 2)

    assert result == {
        "items": [1, 2],
        "next_page": 2
    }

def test_empty_items():
    result = paginate([], 1, 2)

    assert result == {
        "items": [],
        "next_page": None
    }