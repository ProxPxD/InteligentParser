from typing import Callable, Any

from src.nodes.iDefaultStorable import IDefaultStorable
from src.parsingException import ParsingException


class DefaultStorage(IDefaultStorable):

    def __init__(self, default: Any = None):
        self._type: Callable | None = None
        self._get_default: Callable = lambda: default
        self._is_set = False

    def set_type(self, type: Callable | None) -> None:  # TODO: verify if there's a better hinting type
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        self._type = type

    def set_default(self, default: Any) -> None:
        self._is_set = default is not None
        super().set_default(default)

    def set_get_default(self, get_default: Callable) -> None:
        if not isinstance(get_default, Callable):
            raise ParsingException
        if not self._is_set:
            self._is_set = True
        self._get_default = get_default

    def is_set(self) -> bool:
        return self._is_set

    def get(self) -> Any:
        return self._get_default()
