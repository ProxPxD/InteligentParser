import unittest

from tests.categorierTest import CategorierTest
from tests.glosbeTranslatorTest import GlosbeTranslatorTest

tests = [
    GlosbeTranslatorTest,
    CategorierTest,
]


def main():
    for test_class in tests:
        test = test_class()
        unittest.main(module=test, exit=False)


if __name__ == '__main__':
    main()