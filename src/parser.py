from .modeManager import FlagsManager
from .parsingException import ParsingException


class Parser:

    def __init__(self, args: list[str]):
        self._args: list[str] = args[1:]
        self._modesManager = FlagsManager()

    @property
    def modes(self) -> FlagsManager:
        return self._modesManager

    def parse(self):
        self._filter_modes()
        self.validate()

    def _filter_modes(self):
        self._args = self._modesManager.filter_modes_out_of_args(self._args)

    def validate(self) -> bool:
        is_valid, error_messages = self._modesManager.validate_modes()
        is_valid = is_valid and self._validate_args()
        if error_messages:
            raise ParsingException(error_messages)
        return is_valid

    def _validate_args(self) -> bool:
        return True

    def _get_arg(self, i: int, otherwise=None):
        return self._args[i] if i < len(self._args) else otherwise

    def _get_range(self, start: int, end: int = None):
        if end is None:
            return self._args[start:] if 0 < start < len(self._args) else []
        return self._args[start:end] if 0 < start < end < len(self._args) else []
