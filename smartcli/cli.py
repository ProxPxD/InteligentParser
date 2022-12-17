from __future__ import annotations

import shlex
from typing import Iterator, Callable, Iterable

from .nodes.cli_elements import Node, Root, Parameter, HiddenNode, VisibleNode, HelpManager
from .nodes.interfaces import IResetable, any_from_void, bool_from_void


class Cli(IResetable):

    def __init__(self, args: list[str] = None, root: Root | str = None, out=print, **kwargs):
        super().__init__(**kwargs)
        if isinstance(root, str):
            root = Root(root)
        self._root: Root = root or Root()
        self._args: list = args or []
        self._active_nodes = []
        self._action_node: Node = None
        self._is_reset_needed = False
        self._help_manager = HelpManager(self._root, out=out)
        self._used_arity = 0
        self._actions: dict[bool_from_void, any_from_void] = {}

    def set_out_stream(self, out):
        self._help_manager.set_out_stream(out)

    def print_help(self, out=None):
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
        self.parse_without_actions(args)
        self._action_node.perform_all_actions()
        to_return = ParsingResult(self._action_node)  # TODO: finish parsing result
        return to_return

    def parse_without_actions(self, args: list[str] | str = None) -> None:
        self.reset()
        if isinstance(args, str):
            args = shlex.split(args)
        self.set_args(args)
        self._args = self._root.filter_flags_out(self._args)

        self._active_nodes = self._get_active_nodes()
        self._action_node = self._active_nodes[-1]

        node_args = self._get_node_args(self._args)
        node_args = self._action_node.filter_flags_out(node_args)
        self._used_arity = len(node_args)
        self._run_cli_actions()  # Because node arguments count can influence it, TODO: think of refactor
        self._action_node.parse_node_args(node_args)

        self._is_reset_needed = True

    def _get_active_nodes(self) -> list[Node]:
        nodes = list(self._get_active_argument_nodes())
        curr_node = nodes[-1]
        hidden_nodes = list(self._get_active_hidden_nodes(curr_node))
        return nodes + hidden_nodes

    def _get_active_argument_nodes(self) -> Iterator[VisibleNode]:
        i, curr_node = 1, self._root
        yield self._root
        while i < len(self._args) and curr_node.has_visible_node(self._args[i]):
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

    def _get_node_arguments_count(self) -> int:
        return self._used_arity

    def _run_cli_actions(self) -> None:
        for action in self._get_active_actions():
            action()

    def _get_active_actions(self) -> Iterable[Callable]:
        return (action for cond, action in self._actions.items() if cond())

    @property
    def node_arguments_count(self) -> int:
        return self._used_arity

    def reset(self) -> None:
        if self._is_reset_needed:
            for resetable in self._root.get_resetable():
                resetable.reset()
            self._is_reset_needed = False
            self._used_arity = 0

    # Arity conds TODO: add tests

    def when_used_arity_is_odd(self, action: any_from_void) -> None:
        self.when(action, lambda: self._used_arity % 2 == 1)

    def when_used_arity_is_even(self, action: any_from_void) -> None:
        self.when(action, lambda: self._used_arity % 2 == 0)

    def when_used_arity_is_positive(self, action: any_from_void) -> None:
        self.when_used_arity_is_not_equal(action, 0)

    def when_used_arity_is_not_equal(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity != condition_arity)

    def when_used_arity_is_less(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity < condition_arity)

    def when_used_arity_is_less_or_equal(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity <= condition_arity)

    def when_used_arity_is_greater(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity > condition_arity)

    def when_used_arity_is_greater_or_equal(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity >= condition_arity)

    def when_used_arity_is_equal(self, action: any_from_void, condition_arity: int) -> None:
        self.when(action, lambda: self._used_arity == condition_arity)

    def when(self, action: any_from_void, condition: bool_from_void) -> None:
        self._actions[condition] = action


class ParsingResult:  # TODO: implement default values/methods (like name, etc.)

    def __init__(self, node: Node):
        setattr(self, 'node', node)
        setattr(self, 'result', node.get_result())
        for param in node.get_params():
            setattr(self, f'get_{param.name}', ParsingResult.make_getter(param))

    @staticmethod
    def make_getter(param: Parameter):
        return lambda: param.get()
