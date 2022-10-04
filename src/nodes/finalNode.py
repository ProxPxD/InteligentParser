from typing import Any, Callable

from src.nodes.abstractNode import AbstractNode
from src.nodes.defaultStorage import DefaultStorage
from src.nodes.iDefaultStorable import IDefaultStorable
from src.nodes.node import Node
from src.nodes.smartList import SmartList

default_param = str | int | list[str | int] | None


class FinalNode(AbstractNode, IDefaultStorable):

    def __init__(self, name: str, parent: Node, *, limit: int = None, default: default_param = None):
        super().__init__(name)
        self._parent: Node = parent
        self._values = SmartList(limit=limit)
        self._default_storage = DefaultStorage(default)

    def to_list(self):
        self._values = SmartList(limit=None)

    def add_to_values(self, to_add) -> list[str]:
        rest = self._values.filter_out(to_add)
        return rest

    def has_name(self, name: str):
        return name == self.name

    def set_type(self, type: Callable | None) -> None:
        self._default_storage.set_type(type)

    def set_get_default(self, get_default: Callable) -> None:
        self._default_storage.set_get_default(get_default)

    def is_set(self) -> bool:
        return self._default_storage.is_set()

    def get(self) -> Any:
        if self:
            return self._values[0] if len(self._values) == 1 else SmartList(self._values)
        return self._default_storage.get()
