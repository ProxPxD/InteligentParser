import unittest

from tests.abstractTest import AbstractTest
from tests.categorierTest import CategorierTest
from tests.finalNodeTest import FinalNodeTest
from tests.glosbeTranslatorTest import GlosbeTranslatorTest
from tests.nodeTest import NodeTest
from tests.selectingParametersMethodsTest import SelectingParametersMethodsTest

tests = [
    GlosbeTranslatorTest,
    CategorierTest,
    SelectingParametersMethodsTest,
    FinalNodeTest,
    NodeTest,
]


def main():
    failure, errors, total, skipped = 0, 0, 0, 0
    for test_class in tests:
        test = test_class()
        unittest.main(module=test, exit=False)

        failure += test.failure
        errors += test.errors
        total += test.total
        skipped += test.skipped

    print()
    print('#' * (2 * AbstractTest.half_sep_length))
    print('Total test statistics:')
    AbstractTest.print_statistics(failure, errors, skipped, total)


if __name__ == '__main__':
    main()
