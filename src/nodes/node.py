from __future__ import annotations

from abc import ABC
from inspect import signature
from itertools import islice, zip_longest
from typing import Type, Iterator, Callable, Iterable, Any

from src.nodes.interfaces import IName, IResetable
from src.nodes.smartList import SmartList
from src.nodes.storages import IActive, compositeActive, active, bool_func, DefaultStorage, IDefaultStorable
from src.parsingException import ParsingException


def no_empty(func):
    return lambda to_filter: (elem for elem in func(to_filter) if elem)


def flatten_once(func):
    return lambda self, to_flatten: (elem for lst in func(self, to_flatten) for elem in lst)


class ActiveElem(IActive):

    def __init__(self, activated=False):
        self._on_activation = SmartList()
        self._activated = activated

    def activate(self):
        self.set_activated(True)

    def deactivate(self):
        self.set_activated(False)

    def set_activated(self, val: bool):
        self._activated = val
        if self._activated:
            self._call_all_on_activation_functions()

    def _call_all_on_activation_functions(self):
        for func in self._on_activation:
            func()

    def is_active(self):
        return self._activated

    def when_active_add_name_to(self, collection: DefaultSmartStorage):
        if collection is None:
            return
        if not isinstance(collection, DefaultSmartStorage):
            raise ParsingException

        self._on_activation += lambda: collection.append(self.name)


class Node(IName, IResetable, ActiveElem):  # TODO think of splitting the responsibilities

    def __init__(self, name: str):
        IName.__init__(self, name)
        ActiveElem.__init__(self, False)
        self._nodes: dict[str, Node] = {}
        self._hidden_nodes: dict[str, HiddenNode] = {}
        self._flags: dict[str, Flag] = {}
        self._params: dict[str, Parameter] = {}
        self._collections: dict[str, DefaultSmartStorage] = {}
        self._actions: SmartList[Callable] = SmartList()
        self._action_results: list = []
        self._orders: dict[int, list[str]] = {}
        self._default_order: list[str] = []
        self._only_hidden = False

    def reset(self) -> None:
        pass

    def get_resetable(self) -> set[IResetable]:
        resetable = set()
        for collection in [self._nodes, self._hidden_nodes, self._flags, self._params, self._collections]:
            collection = collection.values()
            resetable |= self._get_resetable_from_collection(collection)
        return resetable

    def _get_save(self, name: str, *from_dict: dict[str, stored_by_name]) -> stored_by_name:
        to_return = self._get_stored_by_name(name, *from_dict)
        if to_return is not None:
            return to_return
        raise ValueError(f'Name {name} does not belong to {self.name} ')

    def _put_in_collection(self, to_put: stored_by_name, collection: dict[str, stored_by_name]):
        if to_put.name in collection:
            type_name = to_put.__class__.__name__.__str__()
            raise ValueError(f'{type_name} {to_put.name} already exists in {self._name}')
        collection[to_put.name] = to_put
        return to_put

    def _has_key_in_collection(self, elem: str | stored_by_name, from_dict: dict[str, stored_by_name]) -> bool:
        if isinstance(elem, stored_by_name):
            elem = elem.name
        if not isinstance(elem, str):
            return False
        return elem in from_dict

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

    def _get_stored_by_name(self, name: str, *from_dicts: dict[str, stored_by_name]) -> stored_by_name | None:
        from_dicts = from_dicts if len(from_dicts) else self._get_stored_by_name_collections()
        elems = (elem for dict in from_dicts for elem in dict.values())
        searched = next((elem for elem in elems if elem.has_name(name)), None)
        return searched

    def _get_stored_by_name_collections(self) -> list[dict[str, stored_by_name]]:
        return [self._nodes, self._hidden_nodes, self._params, self._flags, self._collections]

    def add_node(self, to_add: str | Node, action: Callable = None) -> Node:
        node = create_iname(to_add, Node)
        node.add_action(action)
        return self._put_in_collection(node, self._nodes)

    def get_node(self, name: str) -> Node:
        return self._get_save(name, self._nodes, self._hidden_nodes)

    def get_nodes(self) -> list[Node]:
        return list(self._nodes.values())

    def get_all_nodes(self) -> list[Node]:
        return self.get_nodes() + self.get_hidden_nodes()

    def add_flag(self, main: str | Flag, *alternative_names: str, storage: DefaultSmartStorage = None, storage_limit=0, flag_limit=None, default=None) -> Flag:
        flag = create_iname(main, Flag)
        flag.add_alternative_names(*alternative_names)
        flag.set_storage(storage if storage else DefaultSmartStorage(storage_limit, default=default))
        flag.set_limit(flag_limit)
        return self._put_in_collection(flag, self._flags)

    def get_flags(self) -> list[Flag]:
        return list(self._flags.values())

    def get_flag(self, name: str) -> Flag:
        return self._get_save(name, self._flags)

    def set_params(self, *parameters: str | DefaultSmartStorage | Parameter, storages: tuple[DefaultSmartStorage, ...] = ()) -> None:
        for param, storage in zip_longest(parameters, storages):
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

    def get_params(self) -> list[Parameter]:
        return list(self._params.values())

    def add_collection(self, name: str, limit: int = None) -> DefaultSmartStorage:
        collection = DefaultSmartStorage(limit, name=name)
        return self._put_in_collection(collection, self._collections)

    def get_collection(self, name: str) -> DefaultSmartStorage:
        return self._get_save(name, self._collections)

    def get_collections(self) -> list[DefaultSmartStorage]:
        return list(self._collections.values())

    def add_hidden_node(self, to_add: str | Node, active_condition: Callable[[], bool] = None, action: Callable = None) -> HiddenNode:
        node = HiddenNode(to_add, active_condition)
        node.add_action(action)
        self._hidden_nodes[to_add] = node
        return self._hidden_nodes[to_add]

    def get_hidden_node(self, name: str) -> HiddenNode:
        return self._get_save(name, self._hidden_nodes)

    def get_hidden_nodes(self):
        return list(self._hidden_nodes.values())

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
        if next(hidden_nodes, None):
            raise ParsingException("More than one hidden node is active")
        return active

    def __getitem__(self, name: str):
        return self.get(name)

    def __contains__(self, node: str | stored_by_name):
        return self.has(node)

    def has_node(self, node: str | Node) -> bool:
        return self._has_key_in_collection(node, self._nodes)

    def has_flag(self, flag: str | Flag) -> bool:
        flag = str(flag)
        return any(flag_instance.has_name(flag) for flag_instance in self._flags.values())

    def is_flag(self, flag: str):
        return self.has_flag(flag)

    def has_hidden_node(self, hidden_node: str | HiddenNode) -> bool:
        return self._has_key_in_collection(hidden_node, self._hidden_nodes)

    def set_params_order(self, line: str) -> None:
        params = line.split(' ') if len(line) else []
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

    def set_default_setting_order(self, *params: str | Parameter, defaults: list[Any] = None):
        defaults = defaults or []
        for param, default in zip_longest(params, defaults):
            name = str(param)
            self._default_order.append(name)
            if default is not None:
                self.get_param(name).set_default(default)

    ### Parsing

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
        rest = flag.add_to_values(flag_args)
        return rest

    def parse_node_args(self, args: list[str]):
        parameters_number = min(len(args), len(self._params))
        if self._is_parsing_possible(parameters_number):
            self._set_default_order_if_not_exist()
            self._parse_node_args_by_defaults(parameters_number, args)
        elif parameters_number != 0:
            raise ParsingException(self, args)  # TODO: refactor parsing

    def _is_parsing_possible(self, parameters_number: int):
        return parameters_number != 0 and (parameters_number in self._orders or parameters_number >= self._get_obligatory_params_count())

    def _set_default_order_if_not_exist(self) -> None:
        if not self._orders:
            params = self._params.keys()
            self._orders[len(params)] = list(params)

    def _parse_node_args_by_defaults(self, parameters_number: int, args: list[str]):
        needed_defaults, order = self._get_needed_defaults_with_order(parameters_number)
        self._parse_single_args_to_params(args, order, needed_defaults)

    def _get_needed_defaults_with_order(self, parameters_number: int) -> tuple[int, list[str]]:
        closest, order = self._get_closest_arity_with_order(parameters_number)
        return closest - parameters_number, order

    def _get_closest_arity_with_order(self, parameters_number: int) -> tuple[int, list[str]]:
        closest = self._get_closest_arity(parameters_number)
        return closest, self._orders[closest]

    def _get_closest_arity(self, parameters_number: int) -> int:
        return min((num for num in self._orders if num >= parameters_number), default=None)

    def _parse_single_args_to_params(self, args: list[str], order: list[str], needed_defaults: int):
        params_to_use = list(self._get_params_to_use(order, needed_defaults))
        for param, arg in zip(params_to_use, args):
            param.add_to_values(arg)
        rest_of_args = args[len(params_to_use):]
        if not params_to_use and args:
            raise ValueError
        if params_to_use and rest_of_args:
            params_to_use[-1].add_to_values(rest_of_args)

    def _get_params_to_use(self, order: list[str], needed_defaults: int) -> Iterator[Parameter]:
        params_to_skip = self.get_params_to_skip(needed_defaults)
        params_to_use = (self.get_param(param_name) for param_name in order if param_name not in params_to_skip)
        return params_to_use

    def get_params_to_skip(self, needed_defaults: int) -> list[str]:
        to_skip = self._default_order[:needed_defaults]
        lacking_defaults = needed_defaults - len(to_skip)
        to_skip += [param.name for param in islice(self.get_optional_params(), lacking_defaults)]
        return to_skip

    def _parse_list_args_by_order(self, args: list[str], order: list[str]) -> None:
        self.get_param(order[-1]).add_to_values(args)

    # Actions

    def add_action(self, action: Callable) -> None:
        self._actions += action

    def perform_all_actions(self) -> None:
        for action in self._actions:
            arity = len(signature(action).parameters)
            params = (param.get() for param in self._params.values())
            args = list(islice(params, arity))
            result = action(*args)
            self._action_results.append(result)

    def get_action_results(self):
        return self._action_results

    def get_result(self):
        return next(iter(self._action_results), None)


class HiddenNode(Node, IActive):  # TODO: refactor to remove duplications (active and inactive conditions should be a separate class

    def __init__(self, name: str, active_condition: compositeActive = None, inactive_condition: compositeActive = None):
        super().__init__(name)
        self._active_conditions = SmartList(IActive._map_to_single(active_condition)) if active_condition else SmartList()
        self._inactive_conditions = SmartList(IActive._map_to_single(inactive_condition)) if inactive_condition else SmartList()

    def set_active_on_conditions(self, *conditions: compositeActive, func: bool_func = all):
        self._active_conditions += IActive._map_to_single(*conditions, func=func)

    def set_inactive_on_conditions(self, *conditions: compositeActive, func: bool_func = all):
        self._inactive_conditions += IActive._map_to_single(*conditions, func=func)

    def is_active(self) -> bool:
        return all(func() for func in self._active_conditions) and not any(func() for func in self._inactive_conditions)

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
        self.set_active_on_conditions(lambda: all((flag in collection for flag in flags)))
        self.set_inactive_on_flags_in_collection(collection, *but_not, func=any)

    def set_inactive_on_flags_in_collection(self, collection: DefaultSmartStorage, *flags: Flag, func=all):
        self.set_inactive_on_conditions(lambda: func((flag in collection for flag in flags)))


class Root(Node):

    def __init__(self, name: str = 'root'):
        super().__init__(name)


def create_iname(to_create: str | IName, of_type: Type) -> stored_by_name:
    if isinstance(to_create, stored_by_name):
        return to_create
    elif isinstance(to_create, str):
        return of_type(to_create)
    else:
        raise ValueError

###############
# Final nodes #
###############

default_type = str | int | list[str | int] | None


class DefaultSmartStorage(DefaultStorage, SmartList, IName, IResetable):

    def __init__(self, limit: int = None, *, default=None, name=''):
        IName.__init__(self, name)
        SmartList.__init__(self, limit=limit)
        DefaultStorage.__init__(self, default)

    def reset(self):
        self.clear()

    def _get_resetable(self) -> set[IResetable]:
        return set()

    def add_to_add_names(self, *active_elems: ActiveElem):
        for active_elem in active_elems:
            active_elem.when_active_add_name_to(self)

    def get(self):
        to_get = self.copy() if self else super().get()
        return to_get[0] if isinstance(to_get, list) and len(to_get) == 1 else to_get

    def __contains__(self, item):
        if isinstance(item, Flag):
            return any(name in self for name in item.get_all_names())
        return super().__contains__(item)


class FinalNode(IDefaultStorable, IName, IResetable, ActiveElem, ABC):

    def __init__(self, name: str, *, storage: DefaultSmartStorage = None, storage_limit=None, default=None, local_limit=None, activated=False):
        IDefaultStorable.__init__(self)
        IName.__init__(self, name)
        ActiveElem.__init__(self, activated)
        self._limit = local_limit
        self._storage = None
        if storage is not None and any(arg is not None for arg in (storage_limit, default)):
            raise ValueError

        if storage is None:
            storage = DefaultSmartStorage(limit=storage_limit, default=default)

        self._storage = storage

    def reset(self):
        pass

    def _get_resetable(self) -> set[IResetable]:
        return set(self._storage)

    def set_limit(self, limit: int | None, *, storage: DefaultSmartStorage = None) -> None:
        if storage is not None:
            self.set_storage(storage)
        self._limit = limit

    def get_limit(self) -> int:
        return self._limit

    def set_storage_limit(self, limit: int | None, *, storage: DefaultSmartStorage = None) -> None:
        if storage:
            self.set_storage(storage)
        self._storage.set_limit(limit)

    def get_storage_limit(self) -> int:
        return self._storage.get_limit()

    def to_list(self):
        self._storage.set_limit(None)

    def add_to_values(self, to_add) -> list[str]:
        if isinstance(to_add, str) or not isinstance(to_add, Iterable):
            to_add = [to_add]
        rest = self._storage.filter_out(to_add)
        return rest

    def set_storage(self, storage: DefaultSmartStorage):
        self._storage = storage

    def get_storage(self) -> DefaultStorage:
        return self._storage

    def set_type(self, type: Callable | None) -> None:
        self._storage.set_type(type)

    def set_get_default(self, get_default: Callable) -> None:
        self._storage.set_get_default(get_default)

    def add_get_default_if(self, get_default: Callable[[], Any], condition: Callable[[], bool]):
        self._storage.add_get_default_if(get_default, condition)

    def add_get_default_if_and(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        self._storage.add_get_default_if_and(get_default, *conditions)

    def add_get_default_if_or(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        self._storage.add_get_default_if_or(get_default, *conditions)

    def is_default_set(self) -> bool:
        return self._storage.is_default_set()

    def get(self) -> Any:
        to_return = self._storage.get()
        if isinstance(to_return, list) and self._limit is not None and self._limit < len(to_return):
            to_return = to_return[:self._limit]
        if len(to_return) == 1:
            to_return = to_return[0]
        return to_return if to_return else None


class Parameter(FinalNode):

    def __init__(self, name: str, *, storage: DefaultSmartStorage = None, storage_limit: int | None = 1, default: default_type = None, parameter_limit=1):
        super().__init__(name, storage=storage, storage_limit=storage_limit, default=default, local_limit=parameter_limit)
        self.set_activated(True)

    def add_to(self, *nodes: Node):
        for node in nodes:
            node.add_param(self)


class Flag(FinalNode):

    def __init__(self, name, *alternative_names: str, storage: DefaultSmartStorage = None, storage_limit: int = 0, default: default_type = None, local_limit=None):
        super().__init__(name, storage=storage, storage_limit=storage_limit, default=default, local_limit=local_limit, activated=False)
        self._alternative_names = set(alternative_names)
        self._on_activation: SmartList[Callable] = SmartList()

    def reset(self):
        self.deactivate()

    def add_alternative_names(self, *alternative_names: str):
        self._alternative_names |= set(alternative_names)

    def has_name(self, name: str):
        return super().has_name(name) or name in self._alternative_names

    def get_all_names(self) -> list[str]:
        return [self._name] + list(self._alternative_names)


stored_by_name = Node | HiddenNode | Flag | Parameter | DefaultSmartStorage