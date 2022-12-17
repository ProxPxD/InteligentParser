from __future__ import annotations

import abc
from typing import Iterable, Callable, Any


class INamable:

    def __init__(self, name: str = '', **kwargs):
        super().__init__(**kwargs)
        self._name = name

    @property
    def name(self):
        return self._name

    def get_name(self):
        return self._name

    def has_name(self, name: str):
        return name == self.name

    def __str__(self):
        return self._name or self.__class__.__name__


class IResetable(abc.ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abc.abstractmethod
    def reset(self):
        raise NotImplemented

    def _get_resetable(self) -> set[IResetable]:
        raise NotImplemented

bool_from_void = Callable[[], bool]
any_from_void = Callable[[], Any]
any_from_str = Callable[[str], Any]
bool_from_iterable = Callable[[Iterable], bool]


class IDefaultStorable(abc.ABC):

    @abc.abstractmethod
    def set_type(self, type: Callable | None) -> None:  # TODO: verify if there's a better hinting type
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        raise NotImplemented

    @abc.abstractmethod
    def get_type(self) -> Callable:
        raise NotImplemented

    def set_default(self, default: Any) -> None:
        get_default = lambda: default if not isinstance(default, Callable) else default
        self.set_get_default(get_default)

    def set_get_default(self, get_default: Callable) -> None:
        self.add_get_default_if(get_default, lambda: True)

    @abc.abstractmethod
    def add_get_default_if(self, get_default: any_from_void, condition: bool_from_void):
        raise NotImplemented

    @abc.abstractmethod
    def add_get_default_if_and(self, get_default: any_from_void, *conditions: bool_from_void):
        raise NotImplemented

    @abc.abstractmethod
    def add_get_default_if_or(self, get_default: any_from_void, *conditions: bool_from_void):
        raise NotImplemented

    @abc.abstractmethod
    def is_default_set(self) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def get(self) -> Any:
        raise NotImplemented
