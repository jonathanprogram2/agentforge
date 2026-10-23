

from benchmarks.pagination_case.pagination import paginate

def test_last_page():
    result = paginate([1, 2, 3, 4], 2, 2)

    assert result == {
        "items": [3, 4],
        "next_page": None
    }

def test_single_page():
    result = paginate([1, 2], 1, 2)

    assert result == {
        "items": [1, 2],
        "next_page": None
    }