from abstractTest import AbstractTest
from ..src.parserB import ParserB


class BasicNodeTest(AbstractTest):
    @classmethod
    def _get_test_name(cls) -> str:
        return 'Basic node'

    @classmethod
    def setUpClass(cls) -> None:
        super(BasicNodeTest, cls).setUpClass()

        reverse = cls.parserCreator.add_global_flag('-r')
        add = cls.parserCreator.add_node('add')
        add.set_params('number1', 'number2')
        inv = cls.parserCreator.add_node('inv')
        inv.set_params('number')
        cls.parser = ParserB(cls.parserCreator)

    def test_simple_add(self):
        self.parser.parse('add 1 2'.split(' '))
        self.parser.parse()