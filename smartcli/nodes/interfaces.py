from __future__ import annotations

import abc
from typing import Iterable


class IName:

    def __init__(self, name: str = ''):
        self._name = name

    @property
    def name(self):
        return self._name

    def has_name(self, name: str):
        return name == self.name

    def __str__(self):
        return self._name or self.__class__.__name__


class IResetable(abc.ABC):

    @abc.abstractmethod
    def reset(self):
        raise NotImplemented

    def _get_resetable(self) -> set[IResetable]:
        raise NotImplemented

    def _get_resetable_from_collection(self, collection: Iterable[IResetable]) -> set(IResetable):
        return set(resetable for elem in collection for resetable in elem._get_resetable())
