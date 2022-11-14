from __future__ import annotations

from typing import Callable, Any

from smartcli.nodes.interfaces import IActivable, IDefaultStorable


class DefaultStorage(IDefaultStorable):

    def __init__(self, default: Any = None, type: Callable = None, **kwargs):
        super().__init__(**kwargs)
        self._type: Callable | None = type
        self._get_defaults = {lambda: True: lambda: default} if default is not None else {}

    # TODO: add separate type to FinalNode
    # TODO: verify if there's a better hinting type
    def set_type(self, type: Callable | None) -> None:
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        self._type = type

    def get_type(self) -> Callable:
        return self._type

    def add_get_default_if_and(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        condition = IActivable.merge_conditions(conditions, all)
        self.add_get_default_if(condition, get_default)

    def add_get_default_if_or(self, get_default: Callable[[], Any], *conditions: Callable[[], bool]):
        condition = IActivable.merge_conditions(conditions, any)
        self.add_get_default_if(condition, get_default)

    def add_get_default_if(self, get_default: Callable[[], Any], condition: Callable[[], bool]):
        if not isinstance(get_default, Callable):
            raise ValueError
        self._get_defaults[condition] = get_default

    def is_default_set(self) -> bool:
        return len(self._get_defaults) > 0

    def get(self) -> Any:
        to_return = next((get_default() for condition, get_default in reversed(self._get_defaults.items()) if condition()), None)
        return to_return

    def __contains__(self, item):
        if not isinstance(item, (int, float, str, list, dict, set)) and 'name' in item.__dict__:
            item = item.name

        return super().__contains__(item)


