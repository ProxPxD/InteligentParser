from __future__ import annotations

from typing import Type, Iterator, Callable

from src.nodes.abstractNode import AbstractNode
from src.nodes.flag import Flag
from src.nodes.hiddenNode import HiddenNode
from src.nodes.nodeCollection import NodeCollection
from src.nodes.parameter import Parameter
from src.parsingException import ParsingException


def no_empty(func):
    return lambda to_filter: (elem for elem in func(to_filter) if elem)


def flatten_once(func):
    return lambda to_flatten: (elem for lst in func() for elem in lst)


class Node(AbstractNode):  # TODO think of splitting the responsibilities

    def __init__(self, name: str):
        super().__init__(name)
        self._nodes: dict[str, Node] = {}
        self._hidden_nodes: dict[str, HiddenNode] = {}
        self._params: dict[str, Parameter] = {}
        self._flags: dict[str, Flag] = {}
        self._collections: dict[str, NodeCollection] = {}
        self._orders: dict[int, list[str]] = {}
        self._only_hidden = False

    def add_node(self, to_add: str | Node) -> Node:
        return self._add_any_node(to_add, self._nodes, Node)

    def set_only_hidden_nodes(self) -> Node:
        self._only_hidden = True

    def add_collection(self, name: str, limit: int = None) -> NodeCollection:
        self._collections[name] = NodeCollection(limit)
        self._collections[name].set_limit(limit)
        return self._collections[name]

    def add_hidden_node(self, to_add: str | Node, active_condition: Callable[[], bool] = None) -> HiddenNode:
        self._hidden_nodes[to_add] = HiddenNode(to_add, active_condition)
        return self._hidden_nodes[to_add]

    def _get_active_hidden_nodes(self):
        return (node for node in self._hidden_nodes.values() if node.is_condition_met())

    def has_active_hidden_node(self):
        return next(self._get_active_hidden_nodes(), None) is not None

    def get_active_hidden_node(self):
        active = list(self._get_active_hidden_nodes())
        if len(active) > 1:
            raise ParsingException
        return active[1] if active else None

    def add_flag(self, main: str | Flag, *alternative_names: str, arity) -> Flag:
        flag = Flag(main, *alternative_names, max_arity=arity)
        raise NotImplemented

    def get(self, name: str):
        from_dicts = [self._nodes, self._params, self._flags]
        result = next((from_dict[name] for from_dict in from_dicts if name in from_dict), None)
        if not result:
            raise KeyError
        return result

    def __getitem__(self, name: str):
        return self.get(name)

    def get_node(self, name: str) -> Node:
        return self._get_save(name, self._nodes)

    def get_flag(self, name: str) -> Flag:
        return self._get_save(name, self._flags)

    def get_param(self, name: str) -> Parameter:
        return self._get_save(name, self._params)

    def __contains__(self, node):
        return self.has_child_node(node)

    def has_child_node(self, node: str | Node) -> bool:
        return self._has_any_node_type(node, self._nodes, Node)

    def has_flag(self, flag: str | Flag) -> bool:
        return self._has_any_node_type(flag, self._flags, Flag)

    def has_child_node_or_flag(self, node: str | Node):
        return self.has_child_node(node) or self.has_flag(node)

    def is_flag(self, flag: str | Flag):
        return self.has_flag(flag)

    def _has_any_node_type(self, node: str | AbstractNode, from_dict: dict[str, AbstractNode], my_class: Type[AbstractNode] = None) -> bool:
        if isinstance(node, str):
            return node in from_dict.keys()
        if isinstance(node, my_class):
            return node in from_dict.values()
        return False

    def set_params(self, *parameters: str | NodeCollection) -> None:
        for param in parameters:
            self.add_param(param)

    def add_param(self, to_add: str | Parameter | NodeCollection) -> Parameter:
        return self._add_any_node(to_add, self._params, Parameter)

    def set_params_order(self, line: str) -> None:
        params = line.split(' ')
        num = len(params)
        self._orders[num] = params

    def get_optional_params(self) -> list[Parameter]:
        return [param for param in self._params.values() if param.is_set()]

    def _get_obligatory_params_count(self):
        return len(self._params) - len(list(self.get_optional_params()))

    def filter_flags_out(self, args: list[str]) -> list[str]:
        chunks = self._chunk_by_flags(args)
        parameters = next(chunks, [])
        parameters += list(self._filter_flags_out_of_chunks(chunks))
        return parameters

    def _chunk_by_flags(self, args: list[str]) -> Iterator[list[str]]:
        curr_i = 0
        for i, arg in enumerate(args):
            if self.is_flag(arg):
                yield args[curr_i: i]
                curr_i = i
        yield args[curr_i:]

    @flatten_once
    def _filter_flags_out_of_chunks(self, chunks) -> Iterator[list[str]]:
        return (self._filter_flags_out_of_chunk(chunk) for chunk in chunks)

    def _filter_flags_out_of_chunk(self, chunk: list[str]) -> list[str]:
        flag_name, flag_args = chunk[0], chunk[1:]
        flag = self.get_flag(flag_name)
        flag.activate()
        rest = flag.add_to_values(*flag_args)
        return rest

    def parse_node_args(self, args: list[str]):
        parameters_number = min(len(args), len(self._params))
        if parameters_number in self._orders or parameters_number >= self._get_obligatory_params_count():
            self._parse_node_args_by_defaults(parameters_number, args)
        else:
            raise ParsingException(self, args)  # TODO: refactor parsing

    def _parse_node_args_by_defaults(self, parameters_number: int, args: list[str]):
        closest = self._get_closest_order_arity(parameters_number)
        order = self._orders[closest]
        needed_defaults = closest - parameters_number
        params_to_skip = self.get_optional_params()[:needed_defaults]

        self._parse_single_node_args(args, order, params_to_skip)
        self._parse_list_node_args_by_order(args[parameters_number:], order)

    def _get_closest_order_arity(self, parameters_number: int):
        return min(num for num in self._orders if num >= parameters_number)

    def _parse_single_node_args(self, args: list[str], order: list[str], params_to_skip=None):
        if params_to_skip is None:
            params_to_skip = []
        i = 0
        for arg in args:
            param = self.get_param(order[i])
            if param not in params_to_skip:
                param.add_to_values(arg)
            i += 1

    def _parse_list_node_args_by_order(self, args: list[str], order: list[str]):
        param = order[-1]
        for arg in args:
            self.get_param(param).add_to_values(arg)