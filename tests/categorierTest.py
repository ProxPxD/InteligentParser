from parameterized import parameterized

from smartcli.cli import Cli
from smartcli.nodes.cli_elements import Parameter
from tests.abstractTest import AbstractTest


class CategorierTest(AbstractTest):

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

        add_node, del_node, show_node, search_node, rename_node = root.add_nodes('add', 'del', 'show', 'search', 'rename')
        operations.add_to_add_names(add_node, del_node, show_node, search_node, rename_node)
        
        # Examples:
        # "add idea idea_name" == "add idea_name to idea" == "add to idea idea_name
        
        # add (idea|cat|descr)* <NAME> (CAT...) ({to <idea|cat>})* ({-d < DESCR >})
        # del (idea|cat|descr)* < NAME | NUM > ({from <idea|cat>}) *
        # show (idea|cat)* (NAME | NUM)({from <idea|cat>}) ({from < idea | cat >}) *
        # search (idea|cat)* < cat... > ({ in < idea | cat >}) * ({by < cat| descr | name >})
        # rename (idea|cat)* < NAME > < NEW_NAME > ({ in < idea | cat >}) *

        add_node.set_params(operand_param, id_or_name_param, categories)
        del_node.set_params(operand_param, id_or_name_param)
        show_node.set_params(operand_param, id_or_name_param)
        search_node.set_params(operand_param, categories)
        rename_node.set_params(operand_param, id_or_name_param, 'new_name')

        self.is_str = {'idea': '; is idea',
                       'cat': '; is category',
                       'descr': '; is description'}

        op_on_str = '{op} {id} {name}'
        op_with_cats = op_on_str + '; cats: {cats}'
        add_str = op_with_cats.replace('{op}', 'add') + '; descr: {descr}'

        add_idea_str = add_str + self.is_str['idea']
        add_cat_str = add_str + self.is_str['cat']
        add_descr_str = add_str + '; to: {to}' + self.is_str['descr']

        add_idea_str_func = lambda: add_idea_str.format(id=operands.get(), name=id_or_name_param.get(), cats=categories.get_plain(), descr=descriptions.get_plain())
        add_cat_str_func = lambda: add_cat_str.format(id=operands.get(), name=id_or_name_param.get(), cats=categories.get_plain(), descr=descriptions.get_plain())
        add_descr_str_func = lambda: add_descr_str.format(id=operands.get_nth(0), name=id_or_name_param.get(), cats=categories.get_plain(), descr=descriptions.get_plain(), to=operands.get_nth(1) if len(operands.get_plain()) > 1 else '')

        add_node.add_action_when_storables_have_values(add_idea_str_func, operand_param, 'idea')
        add_node.add_action_when_storables_have_values(add_cat_str_func, operand_param, 'cat')
        add_node.add_action(add_descr_str_func, lambda: operands.get() and operands.has('descr'))

        return self.cli

    @parameterized.expand([
        ('idea', ),
        ('cat', ),
        ('descr', ),
    ])
    def test_add_empty(self, type: str, ):
        cli = self.create_correct_cli()
        name = 'test'

        results = cli.parse(f'mem add {type} {name}')
        res = results.result

        self.assertIn(self.is_str[type], res)
        self.assertIn(f'add {type} {name}', res)
        self.assertIn('cats: []', res)
        self.assertIn('descr: []', res)

    @parameterized.expand([('idea', True),
                           ('cat', True),
                           ('descr', False),
                           ])
    def test_add_with_categories_and_descriptions(self, type, with_description):
        cli = self.create_correct_cli()
        name = 'test'
        cat1, cat2, descr1, descr2 = 'cat1', 'cat2', 'description1', 'description2'

        input = f'mem add {type} {name} {cat1} {cat2}'
        if with_description:
            input += f' -d {descr1} {descr2}'
            descr_to_find = str([descr1, descr2])
        else:
            descr_to_find = str([])

        results = cli.parse(input)
        res = results.result

        self.assertIn(self.is_str[type], res)
        self.assertIn(f'add {type} {name}', res)
        self.assertIn(f'cats: {[cat1, cat2]}', res)
        self.assertIn(f'descr: {descr_to_find}', res)

    @parameterized.expand([
        ('idea', ),
        ('cat', ),
        ('descr', ),
    ])
    def test_add_with_to(self, type: str):
        cli = self.create_correct_cli()
        name = 'test'

        results = cli.parse(f'mem add {name} to {type}')
        res = results.result

        self.assertIn(self.is_str[type], res)
        self.assertIn(f'add {type} {name}', res)

    @parameterized.expand([
        ('idea',),
        ('cat',),
        ('descr',),
    ])
    def test_add_idea_with_to_and_categories(self, type):
        cli = self.create_correct_cli()
        name = 'test'
        cat1, cat2 = 'cat1', 'cat2'

        results = cli.parse(f'mem add {name} {cat1} {cat2} to {type}')
        res = results.result

        self.assertIn(self.is_str[type], res)
        self.assertIn(f'add {type} {name}', res)
        self.assertIn(f'cats: {[cat1, cat2]}', res)
