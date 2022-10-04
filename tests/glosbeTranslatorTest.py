from abstractTest import AbstractTest
from src.nodes.root import Root


class GlosbeTranslatorTest(AbstractTest):

    default_mode = None

    @classmethod
    def _get_test_name(cls) -> str:
        return 'Basic node'

    def get_default_mode(self) -> str:
        return self.default_mode

    def set_default_mode(self, mode: str):
        self.default_mode = mode

    def test_create_correct_cli(self):
        #
        root = Root('root')
        root.set_only_hidden_nodes()
        # Collections
        cm = root.add_collection('current_modes')
        cm.set_type(str)
        cm.set_get_default(self.get_default_mode)
        to_langs = root.add_collection('to_langs', 1)
        words = root.add_collection('words')
        from_langs = root.add_collection('from_langs')

        # Flags
        s = root.add_global_flag('--single', '-s')
        w = root.add_global_flag('--word', '-w')
        m = root.add_global_flag('--multi', '-m')
        s.when_active_add_name_to(cm)  # same as 1
        cm.add_to_add_names(m, w)  # same as 1
        w.set_max_arity(None, collection=words)  # infinite
        m.set_max_arity(None, collection=to_langs)  # infinite

        # Hidden nodes
        single_node = root.add_hidden_node('single')
        word_node = root.add_hidden_node('word')
        lang_node = root.add_hidden_node('lang')
        double_multi_node = root.add_hidden_node('double')
        # Hidden nodes activation rules
        single_node.set_active_when_flags(s)
        word_node.set_active_when(lambda: w.is_active())
        word_node.set_inactive_when_flags(m, s)
        lang_node.set_active_when_flags(m, but_not=[w, s])
        double_multi_node.set_active_when_flags(m, w, but_not=s)

        # Params
        # Single's params
        single_node.set_params('word', 'from_lang', 'to_lang')
        single_node.set_params_order('word from_lang to_lang')
        single_node.get_param('from_lang').set_get_default(...)
        single_node.get_param('to_lang').set_get_default(...)
        # Lang's params
        lang_node.set_params_order('words from_lang to_langs')
        lang_node.set_params('word', 'from_lang', 'to_langs')
        lang_node.get_param('from_langs').set_get_default(...)
        lang_node.get_param('to_langs').set_get_default(...)
        lang_node.get_param('to_langs').set_limit(None)
        # Word's params
        # Double's params

    def test_bla_bla(self):
        pass
        # # Params
        # # Single's params
        # single_node.set_params('word', 'from_lang', 'to_lang')
        # single_node.set_params_order('word from_lang to_lang')
        # single_node.get_param('from_lang').set_get_default(...)
        # single_node.get_param('to_lang').set_get_default(...)
        # # Lang's params
        # lang_node.set_params_order('words from_lang to_langs')
        # lang_node.set_params('word', 'from_lang', 'to_langs')
        # lang_node.get_param('from_langs').set_get_default(...)
        # lang_node.get_param('to_langs').set_get_default(...)
        # lang_node.get_param('to_langs').set_limit(None)
        # # Word's params
        # # Double's params

