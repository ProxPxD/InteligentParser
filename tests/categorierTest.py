from smartcli.cli import Cli
from smartcli.nodes.node import Parameter
from tests.abstractTest import AbstractTest


class CategorierTest(AbstractTest):

    @classmethod
    def _get_test_name(cls) -> str:
        return CategorierTest.__class__.__name__.removesuffix('Test')

    def create_correct_cli(self) -> Cli:
        self.cli = Cli()
        root = self.cli.root
        # Collections
        operations = root.add_collection('operations', 1)
        operands = root.add_collection('operands', 2)

        # Flags
        of = root.add_flag('of', 'to', 'from', 'in', storage=operands)
        by = root.add_flag('by', storage_limit=1)
        descriptions = root.add_flag('-d', 'about', storage_limit=None)

        # Common params
        operand_param = Parameter('operand', storage=operands, parameter_limit=1)
        id_param = Parameter('id')
        categories = Parameter('categories', storage_limit=None)

        operand_param.set_inactive_on_flags(of)

        add_node = root.add_node("add")
        del_node = root.add_node("del")
        show_node = root.add_node("show")
        search_node = root.add_node("search")
        rename_node = root.add_node("rename")

        operations.add_to_add_names(add_node, del_node, show_node, search_node, rename_node)

        # add(idea | cat | descr) * < NAME > (CAT...)({to < idea | cat >}) * ({-d < DESCR >})
        # del (idea | cat | descr) * < NAME | NUM > ({from < idea | cat >}) *
        # show(idea | cat) * (NAME | NUM)({from <idea|cat>}) ({from < idea | cat >}) *
        # search(idea | cat) * < cat... > ({ in < idea | cat >}) * ({by < descr | name >})
        # rename(idea | cat) * < NAME > < NEW_NAME > ({ in < idea | cat >}) *

        add_node.set_params(operand_param, id_param, categories)
        del_node.set_params(operand_param, id_param)
        show_node.set_params(operand_param, id_param)
        search_node.set_params(operand_param, categories)
        rename_node.set_params(operand_param, id_param, 'new_name')

        self.is_idea_str = '; is idea'
        self.is_cat_str = '; is category'
        self.is_descr_str = '; is description'

        op_on_str = '{} {} {}'
        op_with_cats = op_on_str + '; cats: {}'
        add_str = op_with_cats.format('add') + '; descr: {}'

        add_idea_str = add_str + self.is_idea_str
        add_cat_str = add_str + self.is_cat_str
        add_descr_str = add_str + '; to: {}' + self.is_descr_str

        add_idea_str = lambda: add_idea_str.format(operands.get(), id_param.get(), categories.get(), descriptions.get())
        add_cat_str = lambda: add_cat_str.format(operands.get(), id_param.get(), categories.get(), descriptions.get())
        add_descr_str = lambda: add_descr_str.format(operands.get_nth(0), id_param.get(), categories.get(), descriptions.get(), operands.get_nth(1) if len(operands.get()) > 1 else 'Not specified')

        add_node.add_action_when_param_has_value(add_idea_str, operands, 'idea')
        add_node.add_action_when_param_has_value(add_cat_str, operands, 'cat')
        add_node.add_action(add_descr_str, lambda: operands.get_first() == 'descr')

        return self.cli

    def test_add_idea(self):
        cli = self.create_correct_cli()
        result = cli.parse('mem add idea test')
        res = result.node.get_result()
        self.assertIn(self.is_idea_str, res)
        self.assertIn('add idea test', res)