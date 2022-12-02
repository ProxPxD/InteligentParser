from __future__ import annotations

import shlex
from typing import Iterator

from .nodes.cli_elements import Node, Root, Parameter, HiddenNode, VisibleNode, HelpManager
from .nodes.interfaces import IResetable


class Cli(IResetable):

    def __init__(self, args: list[str] = None, root: Root = None, **kwargs):
        super().__init__(**kwargs)
        self._root: Root = root or Root()
        self._help_manager = HelpManager(self._root)
        self._args: list = args or []
        self._active_nodes = []
        self._action_node: Node = None
        self._is_reset_needed = False

    def print_help(self, out=print):
        self._help_manager.print_help(out=out)

    def set_args(self, args: list[str]):
        if args:
            self._args[:] = list(args)

    def get_root(self) -> Root:
        return self._root

    root = property(fget=get_root)

    def parse_from_str(self, input: str) -> Node:
        return self.parse(shlex.split(input))

    def parse(self, args: list[str] | str = None) -> Node:
        to_return = self.parse_without_actions(args)
        self._action_node.perform_all_actions()
        return to_return

    def parse_without_actions(self, args: list[str] | str = None):
        self.reset()
        if isinstance(args, str):
            args = shlex.split(args)
        self.set_args(args)
        self._args = self._root.filter_flags_out(self._args)

        self._active_nodes = self._get_active_nodes()
        self._action_node = self._active_nodes[-1]

        node_args = self._get_node_args(self._args)
        node_args = self._action_node.filter_flags_out(node_args)
        self._action_node.parse_node_args(node_args)

        self._is_reset_needed = True
        to_return = ParsingResult(self._action_node)  # TODO: finish parsing result
        return to_return

    def _get_active_nodes(self) -> list[Node]:
        nodes = list(self._get_active_argument_nodes())
        curr_node = nodes[-1]
        hidden_nodes = list(self._get_active_hidden_nodes(curr_node))
        if curr_node.is_hidden_nodes_only() and not hidden_nodes:
            raise ValueError
        return nodes + hidden_nodes

    def _get_active_argument_nodes(self) -> Iterator[VisibleNode]:
        i, curr_node = 1, self._root
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
        if self._is_reset_needed:
            for resetable in self._root.get_resetable():
                resetable.reset()
            self._is_reset_needed = False


class ParsingResult:  # TODO: implement default values/methods (like name, etc.)

    def __init__(self, node: Node):
        setattr(self, 'node', node)
        setattr(self, 'result', node.get_result())
        for param in node.get_params():
            setattr(self, f'get_{param.name}', ParsingResult.make_getter(param))

    @staticmethod
    def make_getter(param: Parameter):
        return lambda: param.get()
