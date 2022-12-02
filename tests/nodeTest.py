from parameterized import parameterized

from smartcli import Node, CliCollection, Cli, Root
from smartcli.exceptions import ValueAlreadyExistsError, IncorrectStateError
from tests.abstractTest import AbstractTest


class NodeTest(AbstractTest):

    def test_action(self):
        node = Node('test')
        node.add_action(lambda: f'{node.name}_{len(node.name)}')

        node.perform_all_actions()

        self.assertEqual('test_4', node.get_result())

    def test_action_with_param(self):
        node = Node('test', parameters=['a'])
        a = node.get_param('a')
        node.add_action(lambda: a.get() * 2)

        node.parse_node_args(['lol'])
        node.perform_all_actions()

        self.assertEqual('lollol', node.get_result())

    def test_action_when_storable_has_no_value(self):
        node = Node('test')
        storable = CliCollection()
        node.add_action_when_storables_have_values(lambda: 'zero', storable, 0)

        node.perform_all_actions()

        self.assertEqual(None, node.get_result())

    def test_action_when_storable_has_value(self):
        node = Node('test')
        storable = CliCollection()
        node.add_action_when_storables_have_values(lambda: 'zero', storable, 0)

        storable += 0
        node.perform_all_actions()

        self.assertEqual('zero', node.get_result())

    def test_only_hidden_nodes_option_with_only_hidden_nodes(self):
        try:
            node = Node('test')
            node.set_only_hidden_nodes()
            node.add_hidden_node('hidden')
        except IncorrectStateError:
            self.fail('Hidden node addition error with only hidden node setting')

    def test_only_hidden_nodes_option_with_visible_nodes_set_after(self):
        node = Node('test')
        node.set_only_hidden_nodes()
        with self.assertRaises(IncorrectStateError):
            node.add_node('visible')

    def test_only_hidden_nodes_option_with_visible_nodes_set_before(self):
        node = Node('test')
        node.add_node('visible')
        with self.assertRaises(IncorrectStateError):
            node.set_only_hidden_nodes()

    @parameterized.expand([('node', Node.add_node),
                           ('flag', Node.add_flag),
                           ('hidden_node', Node.add_hidden_node),
                           ('param', Node.add_param),
                           ('collection', Node.add_collection),
                           ])
    def test_already_existing(self, name, adder):
        node = Node('test')
        adder(node, 'same')
        with self.assertRaises(ValueAlreadyExistsError):
            adder(node, 'same')

    def test_already_existing(self):
        self.run_current_test_with_params()

    def test_no_arg(self):
        cli = Cli()
        cli.parse_without_actions('t')

    def test_no_arg_hidden_node(self):
        root = Root()
        root.set_only_hidden_nodes()
        cli = Cli(root)
        cli.parse_without_actions('t')
