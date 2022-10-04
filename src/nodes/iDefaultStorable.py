import abc
from typing import Callable, Any

from src.parsingException import ParsingException


class IDefaultStorable(abc.ABC):

    @abc.abstractmethod
    def set_type(self, type: Callable | None) -> None:  # TODO: verify if there's a better hinting type
        '''
        Takes a class to witch argument should be mapped
        Takes None if there shouldn't be any type control (default)
        '''
        raise NotImplemented

    def set_default(self, default: Any) -> None:
        self.set_get_default(lambda: default)

    @abc.abstractmethod
    def set_get_default(self, get_default: Callable) -> None:
        raise NotImplemented

    @abc.abstractmethod
    def is_set(self) -> bool:
        raise NotImplemented

    @abc.abstractmethod
    def get(self) -> Any:
        raise NotImplemented
