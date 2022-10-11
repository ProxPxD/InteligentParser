from typing import Iterator

from .nodes.node import Node, Root


class Cli:

    def __init__(self, root: Root, args: list[str] = None):
        self._root: Root = root
        self._args: list = args if args else []
        self._active_nodes = []
        self._action_node: Node = None

    def set_args(self, args: list[str]):
        if args:
            self._args[:] = list(args)

    def parse(self, args: list[str] = None):
        self.set_args(args)
        self._active_nodes = self._get_active_nodes()
        self._action_node = self._active_nodes[-1]

        self._args = self._root.filter_flags_out(self._args)
        node_args = self._get_node_args(self._args)
        node_args = self._action_node.filter_flags_out(node_args)
        self._action_node.parse_node_args(node_args)
        self._action_node.perform_all_actions()

        # self.__dict__['my'] = lambda self: print(self._args)

        return None  # TODO: create return parser object

    def _get_active_nodes(self) -> list[Node]:
        nodes = list(self._get_active_argument_nodes())
        curr_node = nodes[-1]
        hidden_nodes = list(self._get_active_hidden_nodes(curr_node))
        return nodes + hidden_nodes

    def _get_active_argument_nodes(self) -> Iterator[Node]:
        i, curr_node = 0, self._root
        yield self._root
        while self._args and curr_node.has_node(self._args[i]):
            curr_node = curr_node.get_node(self._args[i])
            yield curr_node
            i += 1

    def _get_active_hidden_nodes(self, curr_node: Node):
        while curr_node.has_active_hidden_node():
            curr_node = curr_node.get_active_hidden_node()
            yield curr_node

    def _get_node_args(self, args: list[str]) -> list[str]:
        return args[len(self._active_nodes)-1:]

