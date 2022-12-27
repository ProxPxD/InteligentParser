from parameterized import parameterized

from smartcli import Flag
from smartcli.exceptions import IncorrectArity
from smartcli.nodes.cli_elements import FinalNode, Parameter, CliCollection
from tests.abstractTest import AbstractTest


class FinalNodeTest(AbstractTest):

    @staticmethod
    def name_get_tests(method, param_num, param):
        args: tuple = param.args
        to_add = args[1] if not isinstance(args[1], str) else [args[1]]
        final_node = args[2]
        is_other_than_to_add_length = lambda num: 'many' in base or num is None or num != len(to_add)
        object_limit = final_node.get_limit()
        storage_limit = final_node.get_storage_limit()

        base = f'{method.__name__}_{param_num}'
        base += '_many' if len(to_add) > 1 else '_one'
        if 'plain' in args[3].__name__:
            base += '_plain'
        base += '_to_'
        base += 'flag' if isinstance(final_node, Flag) else 'param'
        if is_other_than_to_add_length(object_limit):
            base += '_with_limit_' + str(object_limit)
        if is_other_than_to_add_length(storage_limit):
            base += '_with_storage_limit_' + str(storage_limit)

        return base

    @parameterized.expand([(['added'], 'added', Flag('0', storage_limit=1), FinalNode.get_plain),
                           ('added', 'added', Flag('1', storage_limit=1), FinalNode.get),
                           (['added1', 'added2'], ['added1', 'added2'], Flag('2', storage_limit=2), FinalNode.get_plain),
                           (['added1', 'added2'], ['added1', 'added2'], Flag('3', storage_limit=2), FinalNode.get),
                           (['added'], 'added', Parameter('4', storage_limit=1), FinalNode.get_plain),
                           ('added', 'added', Parameter('5', storage_limit=1), FinalNode.get),
                           (['added1', 'added2'], ['added1', 'added2'], Parameter('6', storage_limit=2), FinalNode.get_plain),
                           (['added1', 'added2'], ['added1', 'added2'], Parameter('7', storage_limit=2), FinalNode.get),
                           (['added1'], ['added1', 'added2'], Parameter('8', storage=CliCollection(upper_limit=2), parameter_limit=1), FinalNode.get_plain),
                           ('added1', ['added1', 'added2'], Parameter('9', storage=CliCollection(upper_limit=2), parameter_limit=1), FinalNode.get),
                           ],
                          name_func=name_get_tests)
    def test_add_and_get(self, expected, to_add, final_node: FinalNode, getter):
        final_node.add_to_values(to_add)
        self.assertEqual(expected, getter(final_node))

    @parameterized.expand([(IncorrectArity, ['added'], Parameter('0', storage=CliCollection(upper_limit=2), parameter_lower_limit=2), FinalNode.get_plain),
                           (IncorrectArity, ['added'], Parameter('1', storage=CliCollection(upper_limit=2), parameter_lower_limit=2), FinalNode.get),
                           (IncorrectArity, ['added'], Flag('2', storage=CliCollection(lower_limit=2, upper_limit=None)), FinalNode.get_plain),
                           (IncorrectArity, ['added'], Flag('3', storage=CliCollection(lower_limit=2, upper_limit=None)), FinalNode.get),
    ], name_func=name_get_tests)
    def test_raises_when_get(self, expected_exception, to_add, final_node: FinalNode, getter):
        final_node.add_to_values(to_add)
        with self.assertRaises(expected_exception):
            getter(final_node)

    def test_add_and_get(self):
        self.run_current_test_with_params()

    @parameterized.expand([('plain', ['xD'], 'xD', Parameter(''), FinalNode.get_plain, CliCollection()),
                           ('get', 'xD', 'xD', Parameter(''), FinalNode.get, CliCollection()),
                           ('get_plain_with_limit', ['a1'], ['a1', 'a2'], Parameter('', parameter_limit=1), FinalNode.get_plain, CliCollection()),
                           ('get_with_limit', 'a1', ['a1', 'a2'], Parameter('', parameter_limit=1), FinalNode.get, CliCollection()),
                           ])
    def test_outside_storage(self, name, expected, to_add, final_node: FinalNode, getter, outside: CliCollection):
        final_node.set_storage(outside)
        outside += to_add
        self.assertEqual(expected, getter(final_node))

    @parameterized.expand([('of_single_to_int', [3], '3', int, None),
                           ('of_array_to_int', [10, 0], ['10', '0'], int, None),
                           ('wrong_input_to_int', None, 'a', int, ValueError),
                           ('of_single_to_float', [0.5], '0.5', float, None),
                           ('of_array_to_float', [2.5, 0], ['2.5', '0'], float, None),
                           ('wrong_input_float_to_float', None, 'a', float, ValueError),
                           ])
    def test_type_casting(self, name, expected, to_add, type, expected_exception=None):
        final_node = Parameter('', storage_limit=None)
        final_node.set_type(type)
        if not expected_exception:
            final_node.add_to_values(to_add)
            self.assertEqual(expected, final_node.get_plain())
        else:
            with self.assertRaises(expected_exception):
                final_node.add_to_values(to_add)
                final_node.get_plain()

    def test_string_as_return_type(self):
        param = Parameter('test', storage_limit=2)
        param.add_to_values('abc')
        self.assertEqual('abc', param.get())
        self.assertEqual('abc', param.get_nth(0))

    @parameterized.expand([
        ('flag', Flag('main', '-m')),
        ('string', '-m'),
    ])
    def test_default_value_in_flag(self, name: str, to_check: Flag | str):
        storage = CliCollection(default='-m')
        self.assertTrue(to_check in storage)
