from __future__ import annotations

import shlex
from typing import Iterator

from .nodes.interfaces import IResetable
from .nodes.node import Node, Root, Parameter, HiddenNode, VisibleNode


class Cli(IResetable):

    def __init__(self, args: list[str] = None, root: Root = None):
        self._root: Root = root or Root()
        self._args: list = args or []
        self._active_nodes = []
        self._action_node: Node = None

    def set_args(self, args: list[str]):
        if args:
            self._args[:] = list(args)

    def get_root(self) -> Root:
        return self._root

    root = property(fget=get_root)

    def parse_from_str(self, input: str) -> Node:
        return self.parse(shlex.split(input))

    def parse(self, args: list[str] = None) -> Node:
        self.set_args(args)
        self._args = self._root.filter_flags_out(self._args)

        self._active_nodes = self._get_active_nodes()
        self._action_node = self._active_nodes[-1]

        node_args = self._get_node_args(self._args)
        node_args = self._action_node.filter_flags_out(node_args)
        self._action_node.parse_node_args(node_args)
        self._action_node.perform_all_actions()

        return ParsingResult(self._action_node)  # TODO: finish parsing result

    def _get_active_nodes(self) -> list[Node]:
        nodes = list(self._get_active_argument_nodes())
        curr_node = nodes[-1]
        hidden_nodes = list(self._get_active_hidden_nodes(curr_node))
        if curr_node.is_hidden_nodes_only() and not hidden_nodes:
            raise ValueError
        return nodes + hidden_nodes

    def _get_active_argument_nodes(self) -> Iterator[VisibleNode]:
        i, curr_node = 0, self._root
        yield self._root
        while self._args and curr_node.has_visible_node(self._args[i]):
            curr_node = curr_node.get_visible_node(self._args[i])
            curr_node.activate()
            yield curr_node
            i += 1

    def _get_active_hidden_nodes(self, curr_node: Node):
        while curr_node.has_active_hidden_node():
            curr_node = curr_node.get_active_hidden_node()
            yield curr_node

    def _get_node_args(self, args: list[str]) -> list[str]:
        return args[len([node for node in self._active_nodes if not isinstance(node, HiddenNode)]):]

    def reset(self) -> None:
        for resetable in self._root.get_resetable():
            resetable.reset()


class ParsingResult:  # TODO: implement default values/methods (like name, etc.)

    def __init__(self, node: Node):
        setattr(self, 'node', node)
        for param in node.get_params():
            setattr(self, f'get_{param.name}', ParsingResult.make_getter(param))

    @staticmethod
    def make_getter(param: Parameter):
        return lambda: param.get()
