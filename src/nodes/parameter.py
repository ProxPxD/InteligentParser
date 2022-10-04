from __future__ import annotations

from src.nodes.finalNode import FinalNode, default_param
from src.nodes.node import Node


class Parameter(FinalNode):

    def __init__(self, name: str, parent: Node, *, limit: int = None, default: default_param = None):
        super().__init__(name, parent, limit=limit if limit is not None else 1, default=default)

    def set_limit(self, quantity: int | None) -> None:
        self._values.set_limit(quantity)
