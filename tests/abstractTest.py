import abc
import unittest
from itertools import count, takewhile

from smartcli.cli import Cli
from smartcli.nodes.node import Root


class AbstractTest(unittest.TestCase, abc.ABC):

    cli: Cli | None = None
    root: Root | None = None
    half_sep_length = 40

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

        is_error = any(test == self for test, text in result.errors)
        is_failure = any(test == self for test, text in result.failures)
        ok = not (is_error or is_failure)

        print('ok' if ok else 'ERROR' if is_error else 'FAIL' if is_failure else
            'WRONG UNIT TEST OUTCOME CHECKING! Investigate (possible incompatible with a python newer than 3.10)')

    @classmethod
    def _get_test_name(cls) -> str:
        return cls.__name__.removesuffix('Test')

    def run_current_test_with_params(self, *param_num):
        all_names = dir(self)
        method_name = self.get_method_name()
        numbered_names = (f'{method_name}_{i}' for i in count() if not param_num or i in param_num)
        limited_names = takewhile(lambda name: any(actual.startswith(name) for actual in all_names), numbered_names)
        methods = (getattr(self, actual_name) for expected_prefix in limited_names for actual_name in all_names if actual_name.startswith(expected_prefix))

        for method in methods:
            method()
