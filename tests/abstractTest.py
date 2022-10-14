import abc
import unittest

from src.cli import Cli
from src.nodes.node import Root


class AbstractTest(unittest.TestCase, abc.ABC):

    parser: Cli | None = None
    root: Root | None = None
    half_sep_length = 40
    currentResult = None

    @classmethod
    def print_sep_with_text(cls, text: str, sep: str = '*') -> None:
        with_sep_lines = sep * cls.half_sep_length + f' {text} ' + sep * cls.half_sep_length
        over_length = len(with_sep_lines) - cls.half_sep_length*2
        to_print = with_sep_lines[over_length//2 : -over_length//2]
        print(to_print)

    @classmethod
    def setUpClass(cls) -> None:
        cls.print_sep_with_text(f'Starting {cls._get_test_name()} tests!')

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root = None

    def setUp(self) -> None:
        super().setUp()
        print('- ', self.get_method_name(), end=' ... ')

    def get_method_name(self) -> str:
        return self.id().split('.')[-1]

    def tearDown(self) -> None:
        super().tearDown()
        result = self.defaultTestResult()
        self._feedErrorsToResult(result, self._outcome.errors)
        if self.currentResult is not None:
            is_error = any(test == self for test, text in result.errors)
            is_failure = any(test == self for test, text in result.failures)
            ok = not (is_error or is_failure)
            print('ok' if ok else 'ERROR' if is_error else 'FAIL')
        else:
            print()

    def run(self, result: unittest.result.TestResult | None = ...) -> unittest.result.TestResult | None:
        self.currentResult = result
        unittest.TestCase.run(self, result)

    @classmethod
    @abc.abstractmethod
    def _get_test_name(cls) -> str:
        return 'unnamed'

    @abc.abstractmethod
    def test_correct_single_mode(self) -> None:
        pass
