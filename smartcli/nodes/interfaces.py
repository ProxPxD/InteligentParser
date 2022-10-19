from __future__ import annotations

import abc
from typing import Iterable, Callable, Any


class INamable:

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


class IActivable(abc.ABC):

    @staticmethod
    def _map_to_single(*to_map: compositeActive, func: bool_func = all) -> Callable[[], bool] | None:
        if not to_map:
            raise ValueError
        if len(to_map) == 1 and isinstance(to_map[0], Callable):
            return to_map[0]
        if not isinstance(to_map, Iterable):
            to_map = tuple(to_map)
        return IActivable.merge_conditions(to_map, func=func)

    @staticmethod
    def merge_conditions(conditions: tuple[Callable[[], bool], ...], func: Callable[[Iterable], bool]) -> Callable[[], bool]:
        return lambda: func((IActivable._is_met(condition, func) for condition in conditions))

    @staticmethod
    def _is_met(to_check: compositeActive, func: bool_func) -> bool:
        if isinstance(to_check, IActivable):
            return to_check.is_active()
        elif isinstance(to_check, Callable):
            return to_check()
        elif isinstance(to_check, Iterable):
            return IActivable.merge_conditions(tuple(to_check), func)()
        else:
            raise ValueError

    def activate(self):
        self.set_activated(True)

    def deactivate(self):
        self.set_activated(False)

    @abc.abstractmethod
    def set_activated(self, val: bool):
        raise NotImplemented

    @abc.abstractmethod
    def when_active(self, func: Callable) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def is_active(self) -> bool:
        raise NotImplemented


bool_func = Callable[[Iterable], bool]
active = Callable[[], bool] | IActivable
compositeActive = active | Iterable[active]


class IDefaultStorable(abc.ABC):

    @abc.abstractmethod
    def set_type(self, type: Callable | None) -> None:  # TODO: verify if there's a better hinting type
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        raise NotImplemented

    def set_default(self, default: Any) -> None:
        if not isinstance(default, Callable):
            default = lambda: default
        self.set_get_default(default)

    def set_get_default(self, get_default: Callable) -> None:
        self.add_get_default_if(get_default, lambda: True)

    @abc.abstractmethod
    def add_get_default_if(self, get_default: Callable[[], Any], condition: Callable[[], bool]):
        raise NotImplemented

    @abc.abstractmethod
    def add_get_default_if_and(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        raise NotImplemented

    @abc.abstractmethod
    def add_get_default_if_or(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        raise NotImplemented

    @abc.abstractmethod
    def is_default_set(self) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def get(self) -> Any:
        raise NotImplemented
