from __future__ import annotations

import abc
from typing import Callable, Iterable, Any

from smartcli.nodes.smartList import SmartList


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


class IActive(abc.ABC):

    def __init__(self):
        self._on_activation: SmartList[Callable] = SmartList()

    @staticmethod
    def _map_to_single(*to_map: compositeActive, func: bool_func = all) -> Callable[[], bool] | None:
        if not to_map:
            raise ValueError
        if len(to_map) == 1 and isinstance(to_map[0], Callable):
            return to_map[0]
        if not isinstance(to_map, Iterable):
            to_map = tuple(to_map)
        return IActive.merge_conditions(to_map, func=func)

    @staticmethod
    def merge_conditions(conditions: tuple[Callable[[], bool], ...], func: Callable[[Iterable], bool]) -> Callable[[], bool]:
        return lambda: func((IActive._is_met(condition, func) for condition in conditions))

    @staticmethod
    def _is_met(to_check: compositeActive, func: bool_func) -> bool:
        if isinstance(to_check, IActive):
            return to_check.is_active()
        elif isinstance(to_check, Callable):
            return to_check()
        elif isinstance(to_check, Iterable):
            return IActive.merge_conditions(tuple(to_check), func)()
        else:
            raise ValueError

    @abc.abstractmethod
    def is_active(self) -> bool:
        raise NotImplemented


bool_func = Callable[[Iterable], bool]
active = Callable[[], bool] | IActive
compositeActive = active | Iterable[active]


class DefaultStorage(IDefaultStorable):

    def __init__(self, default: Any = None):
        self._type: Callable | None = None
        self._get_defaults = {lambda: True: lambda: default} if default is not None else {}

    def set_type(self, type: Callable | None) -> None:  # TODO: verify if there's a better hinting type
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        self._type = type

    def get_type(self) -> Callable:
        return self._type

    def add_get_default_if_and(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        condition = IActive.merge_conditions(conditions, all)
        self.add_get_default_if(condition, get_default)

    def add_get_default_if_or(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        condition = IActive.merge_conditions(conditions, any)
        self.add_get_default_if(condition, get_default)

    def add_get_default_if(self, get_default: Callable[[], Any], condition: Callable[[], bool]):
        if not isinstance(get_default, Callable):
            raise ValueError
        self._get_defaults[condition] = get_default

    def is_default_set(self) -> bool:
        return len(self._get_defaults) > 0

    def get(self) -> Any:
        return next((get_default() for condition, get_default in self._get_defaults.items() if condition()), None)

    def __contains__(self, item):
        if not isinstance(item, (int, float, str, list, dict, set)) and 'name' in item.__dict__:
            item = item.name

        return super().__contains__(item)


