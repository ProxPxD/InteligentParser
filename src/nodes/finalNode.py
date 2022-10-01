from .abstractNode import AbstractNode
from .node import Node
from .smartList import SmartList

default_param = str | int | list[str | int] | None


class FinalNode(AbstractNode):

    def __init__(self, name: str, parent: Node, *, limit: int = None, default: default_param = None):
        super().__init__(name)
        self._parent: Node = parent
        self._values = SmartList(limit=limit)
        self._default: default_param = None
        self._num_default: int = 0

    def to_list(self):
        self._values = SmartList(limit=None)

    def get(self) -> default_param:
        return self.get_as_arg() if self._values.get_limit() == 1 else self.get_as_list()

    def get_as_list(self) -> list[str | int]:
        return self._values or SmartList(self._default)

    def get_as_arg(self) -> str | int:
        return self._values[0] if len(self._values) else self._default

    def set_default(self, default: default_param):
        self._default = default

    def is_default_set(self):
        return self._default is not None

    def add_to_values(self, to_add) -> list[str]:
        rest = self._values.filter_out(to_add)
        return rest