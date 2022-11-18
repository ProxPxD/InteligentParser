class ParsingException(ConnectionError):
    def __init__(self, validation_messages: list[str] = None, *args):
        super().__init__(*args)
        self.validation_messages = validation_messages if validation_messages else []


class ValueAlreadyExistsError(ValueError):
    def __init__(self, value_type, name: str, *args):
        self.value_type = value_type
        self.name = name
        super().__init__(*args)


class IncorrectStateError(ValueError):
    def __init__(self, reason: str, *args):
        self.reason = reason
        super().__init__(*args)


class IncorrectArity(ValueError):
    def __init__(self, actual: int, expected: str, *args):
        self.actual = actual
        self.expected = expected
        super().__init__(*args)
