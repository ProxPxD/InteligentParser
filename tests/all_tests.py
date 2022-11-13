import unittest

from tests.categorierTest import CategorierTest
from tests.glosbeTranslatorTest import GlosbeTranslatorTest
from tests.selectingParametersMethodsTest import SelectingParametersMethodsTest

tests = [
    GlosbeTranslatorTest,
    CategorierTest,
    SelectingParametersMethodsTest,
]


def main():
    for test_class in tests:
        test = test_class()
        unittest.main(module=test, exit=False)


if __name__ == '__main__':
    main()
