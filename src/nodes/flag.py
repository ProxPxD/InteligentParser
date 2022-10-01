from .finalNode import FinalNode, default_param
from .node import Node


class Flag(FinalNode):

    def __init__(self, name: str, parent: Node, *, limit: int = None, default: default_param = None):
        super().__init__(name, parent, limit=limit if limit is not None else 0, default=default)
        self._is_on: bool = False

    def turn_on(self):
        self.set_is_on(True)

    def turn_off(self):
        self.set_is_on(False)

    def set_is_on(self, val: bool):
        self._is_on = val

    def is_on(self):
        return self._is_on

    def get_max_arity(self):
        return self._values.get_limit()

    def set_max_arity(self, arity: int):
        self._values.set_limit(arity)