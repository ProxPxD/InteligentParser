import operator as op
from functools import reduce

from parameterized import parameterized

from smartcli import Cli, Parameter
from tests.abstractTest import AbstractTest


class SelectingParametersMethodsTest(AbstractTest):
    '''
    Tests compability between:
        * Variable number of parameters
        * Differently set orders
        * Desactivated parameters
        * Default Parameters
    '''

    def create_3_5_paramter_with_mult_at_end(self) -> Cli:
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

    @parameterized.expand([('shorter_order', 10, '7 3'),  # 2
                           ('longer_order', 26, '7 2 3 4'),  # 4
                           ('between_order_mult_param_to_both', 20, '7 3 2'),  # 3
                           ('more_then_longest_many_mult_params', 39, '7 2 3 4 0.5 3')  # >4
                           ])
    def test_variable_parameters_with_orders(self, name, result, argument_string):
        cli = self.create_3_5_paramter_with_mult_at_end()
        two = cli.parse('c ' + argument_string)
        self.assertEqual(result, two.result)

    # def test_variable_parameters_with_orders_and_default_parameters(self):
    #     self.run_current_test_with_params()

    def create_desactivational_cli_with_variable_parameter(self):
        self.cli = Cli()
        root = self.cli.root
        no_end = root.add_flag('--no-end')
        root.set_params_order('seperator ending segments')
        segs: Parameter
        end: Parameter
        sep, end, segs = root.get_params('seperator ending segments')
        root.set_type_to_params(str, sep, end, segs)
        segs.set_limit(None)
        segs.set_lower_limit(0)
        end.set_inactive_on_flags(no_end)

        root.add_action(lambda: sep.get().join(segs.get_plain()) + end.get(), when=end.is_active)
        root.add_action(lambda: sep.get().join(segs.get_plain()), when=end.is_inactive)

        return self.cli

    @parameterized.expand([('base_case', 'poczta.onet.pl', 'join . .pl poczta onet'),
                           ('skip_desactivated', 'poczta.onet.pl', 'join . poczta onet pl --no-end'),
                           ])
    def test_desactivated_params_with_orders_using_variable_parameters(self, name, result, argument_string):
        '''
        desactivated params proceed orders thus the order with desactivated params shall not be taken
        '''
        cli = self.create_desactivational_cli_with_variable_parameter()
        output = cli.parse(argument_string)
        self.assertEqual(result, output.result)

    # TODO: desactivated_params proceed defaults thus the order without them should be used with the defualt one. Check: param count has a desactivated param
    def test_desactivated_params_with_orders_using_default_params(self):
        self.fail('Not implemented yet')

    # TODO: variable params proceeds default. If param count is less the param count with parameters, paramet order should not be used
    def test_variable_params_with_defaults(self):
        self.fail('Not implemented yet')

