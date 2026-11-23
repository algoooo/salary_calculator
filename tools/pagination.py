from collections.abc import Sequence
from typing import TypeVar

T = TypeVar("T")


def paginate(items: Sequence[T], page: int, page_size: int) -> tuple[Sequence[T], int, int]:
    if page_size < 1:
        raise ValueError("Page size must be positive")

    page_count = max(1, (len(items) + page_size - 1) // page_size)
    page = min(max(page, 0), page_count - 1)
    start = page * page_size
    return items[start:start + page_size], page, page_count
