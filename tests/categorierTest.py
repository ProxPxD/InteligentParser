from smartcli.cli import Cli
from smartcli.nodes.node import Root, Parameter
from tests.abstractTest import AbstractTest


class CategorierTest(AbstractTest):

    @classmethod
    def _get_test_name(cls) -> str:
        return CategorierTest.__class__.__name__.removesuffix('Test')

    def create_correct_cli(self) -> Cli:
        root = Root()
        # Collections
        operations = root.add_collection('operations', None)
        operands = root.add_collection('operands', 2)

        # Flags
        of = root.add_flag('of', 'to', 'from', 'in', storage=operands)
        descriptions = root.add_flag('-d', 'about', storage_limit=None)

        # Common params
        operand_param = Parameter('operand', storage=operands, parameter_limit=1)
        id_param = Parameter('id')
        categories = Parameter('categories', storage_limit=None)

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

