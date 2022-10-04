from typing import Callable, Iterable

from src.nodes.flag import Flag
from src.nodes.node import Node
from src.nodes.smartList import SmartList


def _get_reduce_to_bool_and(flags: tuple[Flag]):
    return _get_reduce_to_bool_func(flags, all)


def _get_reduce_to_bool_or(flags: tuple[Flag]):
    return _get_reduce_to_bool_func(flags, any)


def _get_reduce_to_bool_func(flags: tuple[Flag], func: Callable[[Iterable], bool]):
    return lambda: func((flag.is_active() for flag in flags))


def _is_every_condition_met(collection: Iterable):
    return all(func() for func in collection)


class HiddenNode(Node):

    def __init__(self, name: str, active_condition: Callable[[], bool] | tuple[Flag] = None, inactive_condition: Callable[[], bool] | list[Flag] = None):
        super().__init__(name)
        self._when_active = SmartList(self._unify_condition(active_condition))
        self._when_inactive = SmartList(self._unify_condition(inactive_condition))

    def _unify_condition(self, condition: Callable[[], bool] | tuple[Flag]):
        if isinstance(condition, (tuple, list)) and isinstance(condition[0], Flag):
            condition = _get_reduce_to_bool_and(condition)
        return condition

    def set_active_when_flags(self, *flags, but_not=None):
        self.set_active_when_flags_and(*flags)
        self.set_inactive_when_flags(*but_not)

    def set_active_when_flags_and(self, *flags: Flag):
        self.set_active_when(_get_reduce_to_bool_and(flags))

    def set_active_when_flags_or(self, *flags: Flag):
        self.set_active_when(_get_reduce_to_bool_or(flags))

    def set_inactive_when_flags(self, *flags: Flag):
        self.set_inactive_when_flags_and(*flags)

    def set_inactive_when_flags_and(self, *flags: Flag):
        self.set_inactive_when(_get_reduce_to_bool_and(flags))

    def set_inactive_when_flags_or(self, *flags: Flag):
        self.set_inactive_when(_get_reduce_to_bool_and(flags))

    def set_active_when(self, condition: Callable[[], bool]):
        self._when_active += condition

    def set_inactive_when(self, condition: Callable[[], bool]):
        self._when_inactive += condition

    def is_condition_met(self) -> bool:
        return self._is_when_active_condition_met() and not self._is_when_inactive_condition_met()

    def _is_when_active_condition_met(self):
        return _is_every_condition_met(self._when_active)

    def _is_when_inactive_condition_met(self):
        return _is_every_condition_met(self._when_inactive)
