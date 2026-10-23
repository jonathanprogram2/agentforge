

def paginate(items: list[int], page: int, page_size: int) -> dict:
    if page < 1 or page_size < 1:
        raise ValueError("Page and page size must be positive")
    
    start = (page - 1) * page_size
    end = start + page_size

    page_items = items[start:end]

    next_page = page + 1 if end <= len(items) else None

    return {
        "items": page_items,
        "next_page": next_page
    }