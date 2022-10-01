from typing import Callable

from .node import Node


class HiddenNode(Node):

    def __init__(self, name: str, condition: Callable[[], bool] = None):
        super().__init__(name)
        self._condition = condition

    def set_condition(self, condition:  Callable[[], bool]) -> None:
        self._condition = condition

    def is_condition_met(self) -> bool:
        return self._condition()
