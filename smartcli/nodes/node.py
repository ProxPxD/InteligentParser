from __future__ import annotations

from abc import ABC
from inspect import signature
from itertools import islice, zip_longest
from typing import Iterator, Callable, Iterable, Any, TypeVar, Type

from smartcli.exceptions import ParsingException
from smartcli.nodes.interfaces import INamable, IResetable, compositeActive, active, bool_from_iterable, bool_from_void, any_from_void
from smartcli.nodes.smartList import SmartList
from smartcli.nodes.storages import IActivable, DefaultStorage, IDefaultStorable


###########################
# Activations and actions #
###########################

class ImplicitlyActivableMixin(IActivable):

    def __init__(self, activated=False, **kwargs):
        super().__init__(**kwargs)
        self._activated = activated

    def activate(self):
        self.set_activated(True)

    def deactivate(self):
        self.set_activated(False)

    def set_activated(self, val: bool):
        self._activated = val

    def is_active(self) -> bool:
        return self._activated


class ConditionallyActiveMixin(IActivable):

    def __init__(self, active_condition: compositeActive = None, inactive_condition: compositeActive = None, default_state: bool = None, **kwargs):
        super().__init__(**kwargs)
        self._active_conditions = SmartList(self._map_to_single(active_condition)) if active_condition else SmartList()
        self._inactive_conditions = SmartList(self._map_to_single(inactive_condition)) if inactive_condition else SmartList()
        self._default: bool = default_state

    def is_active(self) -> bool:
        if not self._active_conditions and not self._inactive_conditions:
            return self._get_default_state()
        return all(func() for func in self._active_conditions) and not any(func() for func in self._inactive_conditions)

    def _get_default_state(self):
        if self._default is None:
            raise ValueError
        return self._default

    def set_active_on_conditions(self, *conditions: compositeActive, func: bool_from_iterable = all):
        if conditions and conditions[0]:
            self._active_conditions += IActivable._map_to_single(*conditions, func=func)

    def set_inactive_on_conditions(self, *conditions: compositeActive, func: bool_from_iterable = all):
        if conditions and conditions[0]:
            self._inactive_conditions += IActivable._map_to_single(*conditions, func=func)

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

    def set_active_on_flags(self, *flags: Flag, func=any):
        self.set_active_on_conditions(lambda: func([flag.is_active() for flag in flags]))

    def set_inactive_on_flags(self, *flags: Flag, func=any):
        self.set_inactive_on_conditions(lambda: func([flag.is_active() for flag in flags]))

    def set_active_on_flags_in_collection(self, collection: CliCollection, *flags: Flag, but_not: list[Flag] | Flag = None):
        but_not = [but_not] if isinstance(but_not, Flag) else []
        self.set_active_on_conditions(lambda: all((flag in collection for flag in flags)))
        self.set_inactive_on_flags_in_collection(collection, *but_not, func=any)

    def set_inactive_on_flags_in_collection(self, collection: CliCollection, *flags: Flag, func=all):
        self.set_inactive_on_conditions(lambda: func((flag in collection for flag in flags)))


class ActionOnActivationMixin:
    T = TypeVar('T')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._on_activation: SmartList[Callable] = SmartList()

    def when_active_turn_off(self, *to_turn_off: IActivable) -> None:
        self.when_active_set_activated(False, *to_turn_off)

    def when_active_turn_on(self, *to_turn_on: IActivable) -> None:
        self.when_active_set_activated(True, *to_turn_on)

    def when_active_set_activated(self, activated: bool, *to_set: IActivable):
        activate_once = lambda a: a.set_activated(activated)
        self.when_active_apply_for_all(activate_once, to_set)

    def when_active_apply_for_all(self, func: Callable[[T], Any], elems: Iterable[T]):
        self.when_active(lambda: (func(elem) for elem in elems))

    def when_active(self, action: Callable) -> None:
        self._on_activation += action

    def when_active_add_name_to(self, collection: CliCollection) -> None:
        if collection is None:
            return
        if not isinstance(collection, CliCollection):
            raise ParsingException

        self.when_active(lambda: collection.append(self.name))  # TODO has name and IActive?

    def _perform_on_activation(self):
        for func in self._on_activation:
            func()


class ImplicitActionActivation(ImplicitlyActivableMixin, ActionOnActivationMixin):

    def __init__(self, activated=False, **kwargs):
        super().__init__(activated=activated, **kwargs)

    def activate(self):
        super().activate()
        self._perform_on_activation()


class ConditionalActionActivation(ConditionallyActiveMixin, ActionOnActivationMixin):

    def __init__(self, active_condition: compositeActive = None, inactive_condition: compositeActive = None, **kwargs):
        super().__init__(active_condition=active_condition, inactive_condition=inactive_condition, **kwargs)

    def is_active(self) -> bool:
        result = super().is_active()
        if result:
            self._perform_on_activation()
        return result


###########################
# Managers and Containers #
###########################


class FlagManagerMixin:

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._flags: list[Flag] = []

    def __contains__(self, flag: str | Flag):
        return self.has_flag(flag)

    def has_flag(self, flag: str | Flag):
        flag = get_name(flag)
        return any(flag_instance.has_name(flag) for flag_instance in self._flags)

    def __getitem__(self, name: str):
        return self.get_flag(name)

    def get_flag(self, name: str):
        return next((flag for flag in self._flags if flag.has_name(name)))

    def get_flags(self) -> list[Flag]:
        return self._flags

    def add_flag(self, main: str | Flag, *alternative_names: str, storage: CliCollection = None, storage_limit=0, flag_limit=None, default=None) -> Flag:
        name, flag = get_name_and_object_for_namable(main, Flag)
        if self.has_flag(name):  # TODO: check alternative names
            raise ValueError
        flag.add_alternative_names(*alternative_names)
        flag.set_storage(storage if storage else CliCollection(storage_limit, default=default))
        flag.set_limit(flag_limit)
        self._flags.append(flag)
        return flag

    def __len__(self):
        return len(self._flags)

    def filter_flags_out(self, args: list[str]) -> list[str]:
        chunks = self._chunk_by_flags(args)
        parameters = next(chunks, [])
        for chunk in chunks:
            parameters += self._filter_flags_out_of_chunk(chunk)
        return parameters

    def _chunk_by_flags(self, args: list[str]) -> Iterator[list[str]]:
        curr_i = 0
        for i, arg in enumerate(args):
            if self.has_flag(arg):
                yield args[curr_i: i]
                curr_i = i
        yield args[curr_i:]

    def _filter_flags_out_of_chunk(self, chunk: list[str]) -> list[str]:
        flag_name, args = chunk[0], chunk[1:]
        flag = self.get_flag(flag_name)
        flag.activate()
        rest = flag.add_to_values(args)
        return rest


class ParameterManagerMixin:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._params: dict[str, Parameter] = {}
        self._orders: dict[int, list[str]] = {}
        self._default_order: list[str] = []

    def has_param(self, param: str | Parameter):
        name = get_name(param)
        return name in self._params

    def get_param(self, name: str):
        return self._params[name]

    def get_params(self) -> list[Parameter]:
        return list(self._params.values())

    def set_params(self, *parameters: str | CliCollection | Parameter, storages: tuple[CliCollection, ...] = ()) -> None:
        for param, storage in zip_longest(parameters, storages):
            self.add_param(param, storage)

    def add_param(self, to_add: str | Parameter | CliCollection, storage: CliCollection = None) -> Parameter:
        if storage is not None and isinstance(to_add, CliCollection):
            raise ValueError

        if isinstance(to_add, CliCollection):
            storage = to_add
            to_add = to_add.name

        name, param = get_name_and_object_for_namable(to_add, Parameter)
        if name in self._params:
            raise ValueError
        if storage is not None:
            param.set_storage(storage)
        self._params[name] = param
        return param

    def set_params_order(self, line: str) -> None:
        params = line.split(' ') if len(line) else []
        count = len(params)
        if count in self._orders:
            raise ValueError
        self._orders[count] = params

    def get_optional_params(self) -> Iterator[Parameter]:
        return (param for param in self._params.values() if param.is_default_set() or not param.is_active())

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

    def parse_node_args(self, args: list[str]):
        parameters_number = min(len(args), len(self.get_params()))
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
        if not params_to_use and rest_of_args:
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


class HiddenNodeManagerMixin:
    def __init__(self, **kwargs):
        super().__init__()
        self._hidden_nodes: dict[str, HiddenNode] = {}

    def add_hidden_node(self, to_add: str | Node, active_condition: Callable[[], bool] = None, action: Callable = None) -> HiddenNode:
        node = HiddenNode(to_add) if not isinstance(to_add, Node) else to_add
        node.set_active(active_condition)
        node.add_action(action)
        self._hidden_nodes[to_add] = node
        return self._hidden_nodes[to_add]

    def get_hidden_node(self, name: str) -> HiddenNode:
        return self._hidden_nodes[name]

    def get_hidden_nodes(self):
        return list(self._hidden_nodes.values())

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

    def has_hidden_node(self, hidden_node: str | HiddenNode) -> bool:
        name = get_name(hidden_node)
        return name in self._hidden_nodes


#############
# CLI parts #
#############


class Node(INamable, IResetable, ActionOnActivationMixin, ParameterManagerMixin, FlagManagerMixin, HiddenNodeManagerMixin):

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self._visible_nodes: dict[str, VisibleNode] = dict()
        self._collections: dict[str, CliCollection] = dict()
        self._actions: dict[bool_from_void, SmartList[any_from_void]] = dict()
        self._action_results: list = []
        self._only_hidden = False

    # Resetable

    def reset(self) -> None:
        pass

    def get_resetable(self) -> set[IResetable]:
        resetable = set()
        for collection in [self._visible_nodes, self._hidden_nodes, self.get_flags(), self.get_params(), self._collections]:
            collection = collection.values()
            resetable |= set(resetable for elem in collection for resetable in elem._get_resetable())
        return resetable

    # Common

    def __getitem__(self, name: str):
        return self.get(name)

    def get(self, name: str) -> Any:
        for method in self._get_getters_of_all_storages():
            try:
                return method(name)
            except Exception:
                pass
        raise LookupError
    
    def __contains__(self, node: str | INamable):
        return self.has(node)

    def has(self, to_check: str | INamable) -> bool:
        try:
            name = get_name(to_check)
            result = self.get(name)
            return result is not None
        except LookupError:
            return False

    def _get_getters_of_all_storages(self) -> Iterable[Callable[[str], stored_type]]:
        return [self.get_node, self.get_hidden_node, self.get_param, self.get_collection, self.get_flag]

    # Nodes
    def get_node(self, name: str) -> Node:
        return next((nodes[name] for nodes in [self._visible_nodes, self._hidden_nodes] if name in nodes))

    def has_node(self, node: str | Node):
        return self.has_visible_node(node) or self.has_hidden_node(node)

    # Visible Nodes
    def add_node(self, to_add: str | VisibleNode, action: Callable = None) -> VisibleNode:
        name, node = get_name_and_object_for_namable(to_add, VisibleNode)
        if name in self._visible_nodes:
            raise ValueError
        node.add_action(action)
        self._visible_nodes[name] = node
        return node

    def has_visible_node(self, node: str | VisibleNode) -> bool:
        name = get_name(node)
        return name in self._visible_nodes

    def get_visible_node(self, node: str | VisibleNode):
        name = get_name(node)
        return self._visible_nodes[name]

    def get_visible_nodes(self) -> list[Node]:
        return list(self._visible_nodes.values())

    def get_all_nodes(self) -> list[Node]:
        return self.get_visible_nodes() + self.get_hidden_nodes()

    # Only Hiddens
    def set_only_hidden_nodes(self) -> None:
        self._only_hidden = True

    def is_hidden_nodes_only(self):
        return self._only_hidden

    # Collections

    def add_collection(self, name: str, limit: int = None) -> CliCollection:
        self._collections[name] = CliCollection(limit, name=name)
        return self._collections[name]

    def get_collection(self, name: str) -> CliCollection:
        return self._collections[name]

    def get_collections(self) -> list[CliCollection]:
        return list(self._collections.values())

    # Actions

    def add_action_when_param_has_value(self, action: any_from_void, params: Parameter | str | list[Parameter | str], values: str | list[str]):
        params, values = list(params), list(values)
        if len(params) != len(values):
            raise ParsingException

        for param, value in zip(params, values):
            param = self.get_param(param) if isinstance(param, str) else param
            when = lambda: param.get() == value
            self.add_action(action=action, when=when)

    def add_action(self, action: any_from_void, when: bool_from_void = None) -> None:
        when = when or (lambda: True)
        self._actions.setdefault(when, SmartList())
        self._actions[when] += action

    def perform_all_actions(self) -> None:
        for condition, actions in reversed(self._actions.items()):
            if condition():
                self._perform_actions(actions)

    def _perform_actions(self, actions: Iterable[Callable]):
        for action in actions:
            arity = len(signature(action).parameters)
            params = (param.get() for param in self._params.values())
            args = list(islice(params, arity))
            result = action(*args)
            self._action_results.append(result)

    def get_action_results(self):
        return self._action_results

    def get_result(self):
        return next(iter(self._action_results), None)


class VisibleNode(Node, ImplicitActionActivation):

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, activated=False, **kwargs)


class HiddenNode(Node, ConditionalActionActivation):  # TODO: refactor to remove duplications (active and inactive conditions should be a separate class

    def __init__(self, name: str, active_condition: compositeActive = None, inactive_condition: compositeActive = None, **kwargs):
        super().__init__(name=name, active_condition=active_condition, inactive_condition=inactive_condition, **kwargs)


class Root(VisibleNode):

    def __init__(self, name: str = 'root', **kwargs):
        super().__init__(name=name, **kwargs)


class CliCollection(DefaultStorage, SmartList, INamable, IResetable):

    def __init__(self, limit: int = None, *, default=None, name='', **kwargs):
        super().__init__(name=name, limit=limit, default=default, **kwargs)

    def reset(self):
        self.clear()

    def _get_resetable(self) -> set[IResetable]:
        return set()

    def  add_to_add_names(self, *active_elems: ActionOnActivationMixin):
        for active_elem in active_elems:
            active_elem.when_active_add_name_to(self)

    def get(self) -> Any:
        to_get = self.copy() if self else super().get()
        return to_get[0] if isinstance(to_get, list) and len(to_get) == 1 else to_get

    def get_nth(self, n: int):
        return self.get()[n]

    def get_first(self):
        return self.get_nth(0)

    def pop(self, n=0):
        to_return = self.get()
        return to_return[n] if isinstance(to_return, list) else to_return

    def __contains__(self, item):
        if isinstance(item, Flag):
            return any(name in self for name in item.get_all_names())
        return super().__contains__(item)


class FinalNode(IDefaultStorable, INamable, IResetable, ABC):

    def __init__(self, name: str, *, storage: CliCollection = None, storage_limit=None, default=None, local_limit=None, **kwargs):
        IDefaultStorable.__init__(self)
        INamable.__init__(self, name)
        self._limit = local_limit
        self._storage = None
        if storage is not None and any(arg is not None for arg in (storage_limit, default)):
            raise ValueError

        if storage is None:
            storage = CliCollection(limit=storage_limit, default=default)

        self._storage = storage

    def reset(self):
        pass

    def _get_resetable(self) -> set[IResetable]:
        return set(self._storage)

    def set_limit(self, limit: int | None, *, storage: CliCollection = None) -> None:
        if storage is not None:
            self.set_storage(storage)
        self._limit = limit

    def get_limit(self) -> int:
        return self._limit

    def set_storage_limit(self, limit: int | None, *, storage: CliCollection = None) -> None:
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

    def set_storage(self, storage: CliCollection):
        self._storage = storage

    def get_storage(self) -> CliCollection:
        return self._storage

    def set_type(self, type: Callable | None) -> None:
        self._storage.set_type(type)

    def get_type(self) -> Callable:
        return self._storage.get_type()

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


default_type = str | int | list[str | int] | None


class Parameter(FinalNode, ConditionalActionActivation):

    def __init__(self, name: str, *, storage: CliCollection = None, storage_limit: int | None = 1, default: default_type = None, parameter_limit=1):
        super().__init__(name, storage=storage, storage_limit=storage_limit, default=default, local_limit=parameter_limit, default_state=True)

    def add_to(self, *nodes: Node):
        for node in nodes:
            node.add_param(self)


class Flag(FinalNode, ImplicitActionActivation):

    def __init__(self, name, *alternative_names: str, storage: CliCollection = None, storage_limit: int = 0, default: default_type = None, local_limit=None):
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


stored_type = Node | Flag | Parameter | HiddenNode | VisibleNode | CliCollection


def get_name_and_object_for_namable(arg: str | INamable, type: Type) -> tuple[str, stored_type | INamable]:
    if isinstance(arg, str):
        arg = type(name=arg)
    name = arg.name
    return name, arg


def get_name(arg: str | INamable) -> str:
    return arg if isinstance(arg, str) else arg.name