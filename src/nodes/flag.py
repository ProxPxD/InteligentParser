from typing import Callable

from src.nodes.finalNode import FinalNode, default_param
from src.nodes.node import Node
from src.nodes.nodeCollection import NodeCollection
from src.nodes.smartList import SmartList
from src.parsingException import ParsingException


class Flag(FinalNode):

    def __init__(self, name, *alternative_names: str, arity=0, max_arity: int = 0, parent: Node, default: default_param = None):
        super().__init__(name, parent, limit=max_arity, default=default)
        self._alternative_names = alternative_names.copy()
        self._activated: bool = False
        self._on_activation: SmartList[Callable] = SmartList()

    def activate(self):
        self.set_activated(True)

    def deactivate(self):
        self.set_activated(False)

    def set_activated(self, val: bool):
        if val:
            self._call_all_on_activation_functions()
        self._activated = val

    def _call_all_on_activation_functions(self):
        for func in self._on_activation:
            func()

    def is_active(self):
        return self._activated

    def get_max_arity(self):
        return self._values.get_limit()

    def set_max_arity(self, arity: int | None, *, collection: NodeCollection = None):
        if collection:
            self.when_active_add_name_to(collection)
        self._values.set_limit(arity)

    def has_name(self, name: str):
        return super().has_name(name) or name in self._alternative_names

    ## when_active methods
    def when_active_add_name_to(self, collection: NodeCollection):
        if not isinstance(collection, NodeCollection):
            raise ParsingException

        self._on_activation += lambda: collection.append(self.name)
