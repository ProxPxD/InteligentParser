import operator as op
from functools import reduce

from parameterized import parameterized

from smartcli import Cli
from tests.abstractTest import AbstractTest


class SelectingParametersMethodsTest(AbstractTest):
    '''
    Tests compability between:
        * Variable number of parameters
        * Differently set orders
        * Desactivated parameters
        * Default Parameters
    '''

    def create_3_5_paramter_with_multi_at_end(self) -> Cli:
        self.cli = Cli()
        root = self.cli.root
        root.set_params_order('a b mult')
        root.set_params_order('a c b d mult')
        a, b, c, d = root.get_params('a', 'b', 'c', 'd')
        root.get_param('mult').set_limit(None)
        root.get_param('mult').set_default([1])
        root.set_default_to_params(1, 'c', 'd')
        root.set_type_to_params(float, a, b, c, d, 'mult')
        mult = root.get_param('mult')
        root.add_action(lambda: reduce(op.mul, mult.get_plain(), a.get() * c.get() + b.get() * d.get()))
        return self.cli

    @parameterized.expand([('shorter_order', 10, '7 3'),
                           ('longer_order', 26, '7 2 3 4'),
                           ('between_order', 20, '7 2 2'),
                           ('more_then_longest', 39, '7 2 3 4 0.5 3')])
    def test_variable_parameters_with_orders(self, name, result, argument_string):
        cli = self.create_3_5_paramter_with_multi_at_end()
        two = cli.parse('c ' + argument_string)
        self.assertEqual(result, two.result)

    def test_variable_parameters_with_orders(self):
        self.run_current_test_with_params()

    '''
            cli = self.create_3_5_paramter_with_multi_at_end()

            two = cli.parse('c 7 3')
            two_with_mult = cli.parse('c 7 3 2')
            five = cli.parse('c 7 2 3 4')
            five_with_mult = cli.parse('c 7 2 3 4 0.5 3')

            self.assertEqual(10, two.result)
            self.assertEqual(20, two_with_mult.result)
            self.assertEqual(26, five.result)
            self.assertEqual(39, five_with_mult.result)
    '''