from __future__ import annotations

from collections.abc import Iterable
from itertools import islice


class SmartList(list):

    def __init__(self, *to_list, limit: int = None, **kwargs):
        super().__init__(**kwargs)
        self._limit = limit
        if to_list:
            self.extend(to_list)

    def __iadd__(self, elems) -> SmartList:
        elems = [elems] if not isinstance(elems, Iterable) or isinstance(elems, str) else elems
        elems = self._remove_nones(elems)
        elems = self._cut_over_limit(elems)
        super().extend(list(elems))
        return self

    def filter_out(self, elems) -> list:
        self.__iadd__(elems)
        return list(filter(lambda e: e not in self, elems))

    def get_limit(self):
        return self._limit

    def set_limit(self, limit: int | None):
        self._limit = limit
        if limit is not None and len(self) >= limit:
            self[:] = self[:limit]

    def _remove_nones(self, to_filter: Iterable):
        return (elem for elem in to_filter if elem is not None)

    def _cut_over_limit(self, to_cut: Iterable):
        return islice(to_cut, self._get_free_space()) if self._is_limited() else to_cut

    def __add__(self, x) -> SmartList:
        self.extend(x)
        return self

    def append(self, __object) -> None:
        self.__iadd__(__object)

    def extend(self, __iterable: Iterable) -> None:
        self.__iadd__(__iterable)

    def _is_limited(self) -> bool:
        return self._limit is not None

    def _get_free_space(self):
        return self._limit - len(self)

    def __neg__(self):
        to_return = self[0] if len(self) else None
        if to_return:
            self.remove(to_return)
        return to_return
