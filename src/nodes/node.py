from __future__ import annotations

import itertools
from typing import Type, Iterator, Callable, Iterable

from src.nodes.iName import IName
from src.nodes.nodeStorages import Flag, Parameter, DefaultSmartStorage
from src.nodes.smartList import SmartList
from src.nodes.storages import IActive, compositeActive, active, bool_func
from src.parsingException import ParsingException


def no_empty(func):
    return lambda to_filter: (elem for elem in func(to_filter) if elem)


def flatten_once(func):
    return lambda to_flatten: (elem for lst in func() for elem in lst)


class Node(IName):  # TODO think of splitting the responsibilities

    def __init__(self, name: str):
        IName.__init__(self, name)
        self._nodes: dict[str, Node] = {}
        self._hidden_nodes: dict[str, HiddenNode] = {}
        self._params: dict[str, Parameter] = {}
        self._flags: dict[str, Flag] = {}
        self._collections: dict[str, DefaultSmartStorage] = {}
        self._orders: dict[int, list[str]] = {}
        self._only_hidden = False

    def _get_save(self, name: str, from_dict: dict[str, stored_by_name]) -> stored_by_name:
        if name not in from_dict:
            raise ValueError(f'Name {name} does not belong to {self.name} ')
        return from_dict[name]

    def _put_in_collection(self, to_put: stored_by_name, collection: dict[str, stored_by_name]):
        if to_put.name in collection:
            type_name = to_put.__class__.__name__.__str__()
            raise ValueError(f'{type_name} {to_put.name} already exists in {self._name}')
        collection[to_put.name] = to_put
        return to_put

    def _has_in_collection(self, node: str | stored_by_name, from_dict: dict[str, stored_by_name]) -> bool:
        if isinstance(node, stored_by_name):
            node = node.name
        if not isinstance(node, str):
            return False
        return node in from_dict

    def has(self, to_check: str | stored_by_name) -> bool:
        if isinstance(to_check, stored_by_name):
            to_check = to_check.name
        result = self._get_stored_by_name(to_check)
        return result is not None

    def get(self, name: str):
        result = self._get_stored_by_name(name)
        if result is None:
            raise ValueError
        return result

    def _get_stored_by_name(self, name: str) -> stored_by_name | None:
        from_dicts = self._get_stored_by_name_collections()
        return next((from_dict[name] for from_dict in from_dicts if name in from_dict), None)

    def _get_stored_by_name_collections(self) -> list[dict[str, stored_by_name]]:
        return [self._nodes, self._hidden_nodes, self._params, self._flags]

    def add_node(self, to_add: str | Node) -> Node:
        node = create_iname(to_add, Node)
        return self._put_in_collection(node, self._nodes)

    def get_node(self, name: str) -> Node:
        return self._get_save(name, self._nodes)

    def add_flag(self, main: str | Flag, *alternative_names: str, storage: DefaultSmartStorage = None, storage_limit=0, flag_limit=None, default=None) -> Flag:
        flag = create_iname(main, Flag)
        flag.add_alternative_names(*alternative_names)
        flag.set_storage(storage if storage else DefaultSmartStorage(storage_limit, default=default))
        flag.set_limit(flag_limit)
        return self._put_in_collection(flag, self._nodes)

    def get_flag(self, name: str) -> Flag:
        return self._get_save(name, self._flags)

    def set_params(self, *parameters: str | DefaultSmartStorage, storages: tuple[DefaultSmartStorage, ...] = ()) -> None:
        for param, storage in itertools.zip_longest(parameters, storages):
            self.add_param(param, storage)

    def add_param(self, to_add: str | Parameter | DefaultSmartStorage, storage: DefaultSmartStorage = None) -> Parameter:
        if storage is not None and isinstance(to_add, DefaultSmartStorage):
            raise ValueError

        if isinstance(to_add, DefaultSmartStorage):
            storage = to_add
            to_add = to_add.name

        param = create_iname(to_add, Parameter)
        if storage is not None:
            param.set_storage(storage)
        return self._put_in_collection(param, self._params)

    def get_param(self, name: str) -> Parameter:
        return self._get_save(name, self._params)

    def add_collection(self, name: str, limit: int = None) -> DefaultSmartStorage:
        collection = DefaultSmartStorage(limit, name=name)
        return self._put_in_collection(collection, self._collections)

    def add_hidden_node(self, to_add: str | Node, active_condition: Callable[[], bool] = None) -> HiddenNode:
        self._hidden_nodes[to_add] = HiddenNode(to_add, active_condition)
        return self._hidden_nodes[to_add]

    def get_hidden_node(self, name: str) -> HiddenNode:
        return self._get_save(name, self._hidden_nodes)

    def set_only_hidden_nodes(self) -> None:
        self._only_hidden = True

    def _get_active_hidden_nodes(self) -> Iterator[HiddenNode]:
        return (node for node in self._hidden_nodes.values() if node.is_active())

    def has_active_hidden_node(self) -> bool:
        return next(self._get_active_hidden_nodes(), None) is not None

    def get_active_hidden_node(self) -> HiddenNode:
        hidden_nodes = self._get_active_hidden_nodes()
        active = next(hidden_nodes, None)
        if active is None:
            raise ParsingException("None hidden node active")
        if next(hidden_nodes):
            raise ParsingException("More than one hidden node is active")
        return active

    def __getitem__(self, name: str):
        return self.get(name)

    def __contains__(self, node: str | stored_by_name):
        return self.has(node)

    def has_node(self, node: str | Node) -> bool:
        return self._has_in_collection(node, self._nodes)

    def has_flag(self, flag: str | Flag) -> bool:
        return self._has_in_collection(flag, self._flags)

    def is_flag(self, flag: str):
        return self.has_flag(flag)

    def has_hidden_node(self, hidden_node: str | HiddenNode) -> bool:
        return self._has_in_collection(hidden_node, self._hidden_nodes)

    def set_params_order(self, line: str) -> None:
        params = line.split(' ')
        count = len(params)
        if count in self._orders:
            raise ValueError
        self._orders[count] = params

    def get_optional_params(self) -> Iterator[Parameter]:
        return (param for param in self._params.values() if param.is_default_set())

    def _get_optional_params_count(self):
        return len(list(self.get_optional_params()))

    def _get_obligatory_params_count(self):
        return len(self._params) - self._get_optional_params_count()

    def set_allowed_params_default_order(self, *params: str | Parameter):
        raise NotImplemented

    ### Parsing?

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


class HiddenNode(Node, IActive):  # TODO: refactor to remove duplications (active and inactive conditions should be a separate class

    def __init__(self, name: str, active_condition: compositeActive = None, inactive_condition: compositeActive = None):
        super().__init__(name)
        self._active_conditions = SmartList(IActive._map_to_single(active_condition))
        self._inactive_conditions = SmartList(IActive._map_to_single(inactive_condition))

    def set_active_on_conditions(self, *conditions: compositeActive, func: bool_func = all):
        self._active_conditions += IActive._map_to_single(conditions, func=func)

    def set_inactive_on_conditions(self, *conditions: compositeActive, func: bool_func = all):
        self._inactive_conditions += IActive._map_to_single(conditions, func=func)

    def is_active(self) -> bool:
        return all(func() for func in self._active_conditions) and not all(func() for func in self._inactive_conditions)

    def set_active(self, first_when: active, *when: compositeActive, but_not: compositeActive = None):
        self.set_active_and(first_when, *when)
        if but_not:
            self.set_inactive_or(*but_not if isinstance(but_not, Iterable) else but_not)

    def set_active_and(self, *when: compositeActive):
        self.set_active_on_conditions(*when, func=all)

    def set_active_or(self, *when: compositeActive):
        self.set_active_on_conditions(*when, func=any)

    def set_inactive_and(self, *when: compositeActive):
        self.set_inactive_on_conditions(*when, func=all)

    def set_inactive_or(self, *when: compositeActive):
        self.set_inactive_on_conditions(*when, func=any)

    def set_active_on_flags_in_collection(self, collection: DefaultSmartStorage, *flags: Flag, but_not: list[Flag] | Flag = None):
        but_not = list(but_not) if but_not else []
        self.set_active_on_conditions(lambda: all((str(flag) in collection for flag in flags)))
        self.set_inactive_on_conditions(lambda: any((str(flag) in collection for flag in but_not)))

    def set_inactive_on_flags_in_collection(self, collection: DefaultSmartStorage, *flags: Flag):
        self.set_inactive_on_conditions(lambda: all((str(flag) in collection for flag in flags)))


class Root(Node):

    def __init__(self, name: str = 'root'):
        super().__init__(name)

    def add_global_flag(self, main: str | Flag, *alternative_names: str) -> Flag:
        return self.add_flag(main, *alternative_names)

    def get_global_flag(self, name: str) -> Flag:
        return self.get_flag(name)


def create_iname(to_create: str | IName, of_type: Type) -> stored_by_name:
    if isinstance(to_create, stored_by_name):
        return to_create
    elif isinstance(to_create, str):
        return of_type(to_create)
    else:
        raise ValueError


stored_by_name = Node | HiddenNode | Flag | Parameter | DefaultSmartStorage
