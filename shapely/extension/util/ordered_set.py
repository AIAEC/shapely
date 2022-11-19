from collections import OrderedDict
from contextlib import suppress
from typing import Optional, Sequence, Any, Union, Set


class OrderedSet:
    def __init__(self, items: Optional[Sequence[Any]] = None):
        self._dict = OrderedDict()
        for item in items or []:
            self._dict[item] = None

    def __contains__(self, item):
        return item in self._dict

    def __bool__(self):
        return bool(self._dict)

    def __iter__(self):
        return iter(self._dict.keys())

    def __len__(self) -> int:
        return len(self._dict)

    def pop(self) -> Any:
        return self._dict.popitem()[0]

    def add(self, item):
        self._dict[item] = None

    def difference_update(self, items: Union[Sequence[Any], Set[Any]]):
        for item in items:
            with suppress(KeyError):
                self._dict.pop(item)

    def discard(self, item):
        if item not in self._dict:
            return
        self._dict.pop(item)
