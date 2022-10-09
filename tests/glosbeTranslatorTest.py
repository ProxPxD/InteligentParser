from abstractTest import AbstractTest
from src.nodes.node import Root


class GlosbeTranslatorTest(AbstractTest):

    default_mode: str = None
    langs: list[str] = []
    limit: int = 4
    words = []

    @classmethod
    def _get_test_name(cls) -> str:
        return 'Basic node'

    def get_default_mode(self) -> str:
        return self.default_mode

    def get_nth_lang(self, n: int) -> str:
        return self.langs[n]

    def get_first_n_langs(self, n) -> list[str]:
        return self.langs[:n] if n < len(self.langs) else self.langs

    def test_create_correct_cli(self):
        #
        root = Root('root')
        root.set_only_hidden_nodes()
        # Collections
        current_modes = root.add_collection('current_modes')
        current_modes.set_type(str)
        current_modes.set_get_default(self.get_default_mode)
        from_langs = root.add_collection('from_langs', 1)
        to_langs = root.add_collection('to_langs')
        words = root.add_collection('words')

        # Flags
        s = root.add_global_flag('--single', '-s')
        w = root.add_global_flag('--word', '-w')
        m = root.add_global_flag('--multi', '-m')
        s.when_active_add_name_to(current_modes)  # same as 1
        current_modes.add_to_add_names(m, w)  # same as 1
        w.set_limit(None, storage=words)  # infinite
        m.set_limit(None, storage=to_langs)  # infinite

        # Hidden nodes
        single_node = root.add_hidden_node('single')
        word_node = root.add_hidden_node('word')
        lang_node = root.add_hidden_node('lang')
        double_multi_node = root.add_hidden_node('double')
        # Hidden nodes activation rules
        single_node.set_active_on_flags_in_collection(current_modes, s, but_not=[w, m])
        word_node.set_active_on_flags_in_collection(current_modes, w)
        word_node.set_inactive_on_flags_in_collection(current_modes, m, s)
        lang_node.set_active_on_flags_in_collection(current_modes, m, but_not=w)
        double_multi_node.set_active_on_flags_in_collection(current_modes, m, w, but_not=s)

        # Params
        from_langs.set_get_default(lambda: self.get_nth_lang(0))
        to_langs.add_get_default_if_or(lambda: self.get_nth_lang(1), single_node.is_active, word_node.is_active)
        to_langs.add_get_default_if_or(lambda: self.get_first_n_langs(self.limit), lang_node.is_active, double_multi_node.is_active)
        # Single's params
        single_node.set_params_order('word from_lang to_lang')
        single_node.set_params_order('word to_lang')
        single_node.set_params_order('word')
        single_node.set_params('word', 'from_lang', 'to_lang', storages=(words, from_langs, to_langs))
        # Lang's params
        lang_node.set_params('word', 'from_lang', 'to_langs', storages=(words, from_langs, to_langs))
        lang_node.set_params_order('words from_lang to_langs')
        lang_node.set_allowed_params_default_order('from_lang')
        # Word's params
        word_node.set_params('word', 'from_lang', 'to_langs', storages=(words, from_langs, to_langs))
        word_node.set_params_order('from_lang to_langs words')
        lang_node.set_allowed_params_default_order('from_lang', 'to_langs')
        # Double's params
        double_multi_node.set_params('word', 'from_lang', 'to_langs', storages=(words, from_langs, to_langs))
        double_multi_node.set_params_order('from_lang')
        double_multi_node.set_params_order('')


    def test_cloning_node(self):
        pass
        # test functionality of creating the same node until some point

    def test_bla_bla(self):
        pass
        # # Hidden nodes activation rules
        # single_node.set_active(s)
        # word_node.set_active_on_conditions(lambda: w.is_active())
        # word_node.set_inactive_or(m, s)
        # lang_node.set_active(m, but_not=[w, s])
        # double_multi_node.set_active(m, w, but_not=s)
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

