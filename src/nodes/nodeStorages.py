from __future__ import annotations

from typing import Callable, Any, Sized

from src.nodes.iName import IName
from src.nodes.smartList import SmartList
from src.nodes.storages import DefaultStorage, IDefaultStorable, IActive
from src.parsingException import ParsingException

default_type = str | int | list[str | int] | None


class DefaultSmartStorage(DefaultStorage, SmartList, IName):

    def __init__(self, limit: int = None, *, default=None, name=''):
        IName.__init__(self, name)
        SmartList.__init__(self, limit=limit)
        DefaultStorage.__init__(self, default)

    def add_to_add_names(self, *flags: Flag):
        for flag in flags:
            flag.when_active_add_name_to(self)

    def get(self):
        to_get = SmartList(self if self else super().get())
        return to_get[0] if isinstance(to_get, list) and len(to_get) == 1 else SmartList(to_get)

    def has_flag(self, flag: Flag | str):
        return str(flag) in self


class FinalNode(IDefaultStorable, IName):

    def __init__(self, name: str, *, storage: DefaultSmartStorage = None, limit=None, default=None, local_limit=None):
        IDefaultStorable.__init__(self)
        IName.__init__(self, name)
        self._limit = local_limit
        self._storage = None
        if storage is not None and any(arg is not None for arg in (limit, default)):
            raise ValueError

        if storage is None:
            storage = DefaultSmartStorage(limit=limit, default=default)

        self._storage = storage

    def set_limit(self, limit: int | None, *, storage: DefaultSmartStorage = None) -> None:
        if storage is not None:
            self.set_storage(storage)
        self._limit = limit

    def get_limit(self) -> int:
        return self._limit

    def set_storage_limit(self, limit: int | None, *, storage: DefaultSmartStorage = None) -> None:
        if storage:
            self.set_storage(storage)
        self._storage.set_limit(limit)

    def get_storage_limit(self) -> int:
        return self._storage.get_limit()

    def to_list(self):
        self._storage.set_limit(None)

    def add_to_values(self, to_add) -> list[str]:
        rest = self._storage.filter_out(to_add)
        return rest

    def set_storage(self, storage: DefaultSmartStorage):
        self._storage = storage

    def get_storage(self) -> DefaultStorage:
        return self._storage

    def set_type(self, type: Callable | None) -> None:
        self._storage.set_type(type)

    def set_get_default(self, get_default: Callable) -> None:
        self._storage.set_get_default(get_default)

    def add_get_default_if(self, get_default: Callable[[], Any], condition: Callable[[], bool]):
        self._storage.add_get_default_if(get_default, condition)

    def add_get_default_if_and(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        self._storage.add_get_default_if_and(get_default, *conditions)

    def add_get_default_if_or(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        self._storage.add_get_default_if_or(get_default, *conditions)

    def is_default_set(self) -> bool:
        return self._storage.is_default_set()

    def get(self) -> Any:
        to_return = self._storage.get()
        if isinstance(to_return, list) and self._limit is not None and self._limit < len(to_return):
            to_return = to_return[:self._limit]
        if len(to_return) == 1:
            to_return = to_return[0]
        return to_return if to_return else None


class Parameter(FinalNode):

    def __init__(self, name: str, *, storage: DefaultSmartStorage = None, limit: int = 1, default: default_type = None, local_limit=1):
        super().__init__(name, storage=storage, limit=limit, default=default, local_limit=local_limit)


class Flag(FinalNode, IActive):

    def __init__(self, name, *alternative_names: str, storage: DefaultSmartStorage = None, storage_limit: int = 0, default: default_type = None, local_limit=None):
        super().__init__(name, storage=storage, limit=storage_limit, default=default, local_limit=local_limit)
        self._alternative_names = set(alternative_names)
        self._activated: bool = False
        self._on_activation: SmartList[Callable] = SmartList()

    def add_alternative_names(self, *alternative_names: str):
        self._alternative_names |= set(alternative_names)

    def activate(self):
        self.set_activated(True)

    def deactivate(self):
        self.set_activated(False)

    def set_activated(self, val: bool):
        self._activated = val
        if val:
            self._call_all_on_activation_functions()

    def _call_all_on_activation_functions(self):
        for func in self._on_activation:
            func()

    def is_active(self):
        return self._activated

    def has_name(self, name: str):
        return super().has_name(name) or name in self._alternative_names

    def when_active_add_name_to(self, collection: DefaultSmartStorage):
        if not collection:
            return
        if not isinstance(collection, DefaultSmartStorage):
            raise ParsingException

        self._on_activation += lambda: collection.append(self.name)
