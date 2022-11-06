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
        descriptions = root.add_flag('-d', 'about', storage_limit=None, default=[])

        # Common params
        operand_param = Parameter('operand', storage=operands, parameter_limit=1)
        id_or_name_param = Parameter('id_or_name')
        categories = Parameter('categories', storage_limit=None, parameter_lower_limit=0, parameter_limit=None, default=[])

        operand_param.set_inactive_on_flags(of)

        add_node = root.add_node("add")
        del_node = root.add_node("del")
        show_node = root.add_node("show")
        search_node = root.add_node("search")
        rename_node = root.add_node("rename")

        operations.add_to_add_names(add_node, del_node, show_node, search_node, rename_node)
        
        # Examples:
        # "add idea idea_name" == "add idea_name to idea" == "add to idea idea_name
        
        # add (idea|cat|descr)* <NAME> (CAT...) ({to <idea|cat>})* ({-d < DESCR >})
        # del (idea|cat|descr)* < NAME | NUM > ({from <idea|cat>}) *
        # show (idea|cat)* (NAME | NUM)({from <idea|cat>}) ({from < idea | cat >}) *
        # search (idea|cat)* < cat... > ({ in < idea | cat >}) * ({by < descr | name >})
        # rename (idea|cat)* < NAME > < NEW_NAME > ({ in < idea | cat >}) *

        add_node.set_params(operand_param, id_or_name_param, categories)
        del_node.set_params(operand_param, id_or_name_param)
        show_node.set_params(operand_param, id_or_name_param)
        search_node.set_params(operand_param, categories)
        rename_node.set_params(operand_param, id_or_name_param, 'new_name')

        self.is_idea_str = '; is idea'
        self.is_cat_str = '; is category'
        self.is_descr_str = '; is description'

        op_on_str = '{op} {id} {name}'
        op_with_cats = op_on_str + '; cats: {cats}'
        add_str = op_with_cats.replace('{op}', 'add') + '; descr: {descr}'

        add_idea_str = add_str + self.is_idea_str
        add_cat_str = add_str + self.is_cat_str
        add_descr_str = add_str + '; to: {}' + self.is_descr_str

        add_idea_str_func = lambda: add_idea_str.format(id=operands.get(), name=id_or_name_param.get(), cats=categories.get_plain(), descr=descriptions.get_plain())
        add_cat_str_func = lambda: add_cat_str.format(operands.get(), id_or_name_param.get(), categories.get_plain(), descriptions.get_plain())
        add_descr_str_func = lambda: add_descr_str.format(operands. get_nth(0), id_or_name_param.get(), categories.get_plain(), descriptions.get_plain(), operands.get_nth(1) if len(operands.get()) > 1 else 'Not specified')

        add_node.add_action_when_storable_has_value(add_idea_str_func, operand_param, 'idea')
        add_node.add_action_when_storable_has_value(add_cat_str_func, operand_param, 'cat')
        add_node.add_action(add_descr_str_func, lambda: operands.get() and operands.has('descr'))

        return self.cli

    def test_add_empty_idea(self):
        cli = self.create_correct_cli()
        name = 'test'

        results = cli.parse(f'mem add idea {name}')
        res = results.result

        self.assertIn(self.is_idea_str, res)
        self.assertIn(f'add idea {name}', res)
        self.assertIn('cats: []', res)
        self.assertIn('descr: []', res)

    def test_add_idea_with_categories_and_descriptions(self):
        cli = self.create_correct_cli()
        name = 'test'
        cat1, cat2, descr1, descr2 = 'cat1', 'cat2', 'description1', 'description2'

        results = cli.parse(f'mem add idea {name} {cat1} {cat2} -d {descr1} {descr2}')
        res = results.result

        self.assertIn(self.is_idea_str, res)
        self.assertIn(f'add idea {name}', res)
        self.assertIn(f'cats: {[cat1, cat2]}', res)
        self.assertIn(f'descr: {[descr1, descr2]}', res)

    def test_add_idea_with_to(self):
        cli = self.create_correct_cli()
        name = 'test'

        results = cli.parse(f'mem add {name} to idea')
        res = results.result

        self.assertIn(self.is_idea_str, res)
        self.assertIn(f'add idea {name}', res)

    def test_add_idea_with_to_and_categories(self):
        cli = self.create_correct_cli()
        name = 'test'
        cat1, cat2 = 'cat1', 'cat2'

        results = cli.parse(f'mem add {name} {cat1} {cat2} to idea')
        res = results.result

        self.assertIn(self.is_idea_str, res)
        self.assertIn(f'add idea {name}', res)
        self.assertIn(f'cats: {[cat1, cat2]}', res)
