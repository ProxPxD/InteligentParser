from typing import Iterator

from .flagsManager import FlagsManager
from .nodes.node import Node
from .nodes.root import Root


class ParserB:

    def __init__(self, root: Root, args: list[str] = None):
        self._root: Root = root
        self._args: list = args if args else []
        self._active_nodes = []
        self._action_node: Node = None
        self._flags_manager = FlagsManager()

    @property
    def flags(self) -> FlagsManager:
        return self._flags_manager

    def set_args(self, args: list[str]):
        if args:
            self._args[:] = list(args)

    def parse(self, args: list[str] = None):
        self.set_args(args)
        self._active_nodes = list(self._get_active_nodes())
        self._action_node = self._active_nodes[-1]

        self._args = self._root.filter_flags_out(self._args)
        node_args = self._get_node_args(self._args)
        node_args = self._action_node.filter_flags_out(node_args)
        self._action_node.parse_node_args(node_args)
        return None  # TODO: create return parser object

    def _get_active_nodes(self) -> Iterator[Node]:
        i, curr_node = 0, self._root
        yield self._root
        while curr_node.has_child_node(self._args[i]):
            curr_node = curr_node.get_node(self._args[i])
            yield curr_node
            i += 1

        while curr_node.has_active_hidden_node():
            curr_node = curr_node.get_active_hidden_node()
            yield curr_node

    def _get_node_args(self, args: list[str]) -> list[str]:
        return args[len(self._active_nodes)-1:]

