from __future__ import annotations

from typing import Iterable, List, Mapping, Sequence, Tuple, TypeVar

T = TypeVar("T")


def first_items(items: Sequence[T] | Iterable[T], limit: int) -> List[T]:
    output: List[T] = []
    for item in items:
        output.append(item)
        if len(output) >= limit:
            break
    return output


def sort_dict_desc(values: Mapping[str, float]) -> List[Tuple[str, float]]:
    return sorted(values.items(), key=lambda item: item[1], reverse=True)
