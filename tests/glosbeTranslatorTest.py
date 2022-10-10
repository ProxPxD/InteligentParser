from abstractTest import AbstractTest
from src.cli import Cli
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
        # ############### #
        # Parser creation #
        # ############### #
        root = Root('root')
        root.set_only_hidden_nodes()
        # Collections
        current_modes = root.add_collection('current_modes')
        current_modes.set_type(str)
        self.default_mode = 'before get mode'
        current_modes.set_get_default(self.get_default_mode)
        from_langs = root.add_collection('from_langs', 1)
        to_langs = root.add_collection('to_langs')
        words = root.add_collection('words')

        self.assertEqual(current_modes, root.get_collection('current_modes'), msg='Collection got wrongly')
        self.default_mode = 'after get mode'
        self.assertEqual(self.default_mode, current_modes.get(), msg="Collection's default has not been returned correctly")
        self.assertEqual(from_langs, root.get('from_langs'), msg='Collection got wrongly')
        self.assertEqual(to_langs, root.get_collection('to_langs'), msg='Collection got wrongly')
        self.assertEqual(words, root.get_collection('words'), msg='Collection got wrongly')
        self.assertEqual(1, from_langs.get_limit(), msg='limit is set wrongly')

        # Flags
        single_flag = root.add_global_flag('--single', '-s')
        word_flag = root.add_global_flag('--word', '-w')
        lang_flag = root.add_global_flag('--multi', '-m')
        single_flag.when_active_add_name_to(current_modes)  # same as 1
        current_modes.add_to_add_names(lang_flag, word_flag)  # same as 1
        word_flag.set_limit(None, storage=words)  # infinite
        lang_flag.set_limit(None, storage=to_langs)  # infinite

        self.assertEqual(3, len(root.get_all_flags()), msg='Flags have not been added')
        self.assertEqual(single_flag, root.get_flag('--single'), msg='Flag got wrongly by the main name')
        self.assertEqual(single_flag, root.get('-s'), msg='Flag got wrongly by an alternative name')
        self.assertEqual(word_flag, root.get('--word'), msg='Flag got wrongly by the main name')
        self.assertEqual(word_flag, root.get_flag('-w'), msg='Flag got wrongly by an alternative name')
        self.assertEqual(lang_flag, root.get_flag('--multi'), msg='Flag got wrongly by the main name')
        self.assertEqual(lang_flag, root.get('-m'), msg='Flag got wrongly by an alternative name')

        self.assertEqual(None, word_flag.get_limit(), msg='Flag has a wrong limit assigned')
        self.assertEqual(words, word_flag.get_storage(), msg='Flag has a wrong storage assigned')
        self.assertEqual(None, lang_flag.get_limit(), msg='Flag has a wrong limit assigned')
        self.assertEqual(to_langs, lang_flag.get_storage(), msg='Flag has a wrong storage assigned')

        test_string = 'test'
        words.append(test_string)
        self.assertEqual(test_string, word_flag.get(), msg='Flag has a storage that is not the same place as the original one')
        words.clear()

        # Hidden nodes
        single_node = root.add_hidden_node('single')
        word_node = root.add_hidden_node('word')
        lang_node = root.add_hidden_node('lang')
        double_multi_node = root.add_hidden_node('double')

        self.assertEqual(single_node, root.get_hidden_node('single'), msg='Hidden node got wrongly')
        self.assertEqual(word_node, root.get('word'), msg='Hidden node got wrongly')
        self.assertEqual(lang_node, root.get_hidden_node('lang'), msg='Hidden node got wrongly')
        self.assertEqual(double_multi_node, root.get('double'), msg='Hidden node got wrongly')

        # Hidden nodes activation rules
        single_node.set_active_on_flags_in_collection(current_modes, single_flag, but_not=[word_flag, lang_flag])
        word_node.set_active_on_flags_in_collection(current_modes, word_flag)
        word_node.set_inactive_on_flags_in_collection(current_modes, lang_flag, single_flag)
        lang_node.set_active_on_flags_in_collection(current_modes, lang_flag, but_not=word_flag)
        double_multi_node.set_active_on_flags_in_collection(current_modes, lang_flag, word_flag, but_not=single_flag)

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
        lang_node.set_default_setting_order('from_lang')
        # Word's params
        word_node.set_params('word', 'from_lang', 'to_langs', storages=(words, from_langs, to_langs))
        word_node.set_params_order('from_lang to_langs words')
        lang_node.set_default_setting_order('from_lang', 'to_langs')
        # Double's params
        double_multi_node.set_params('word', 'from_lang', 'to_langs', storages=(words, from_langs, to_langs))
        double_multi_node.set_params_order('from_lang')
        double_multi_node.set_params_order('')

        # ######################### #
        # Complete argument parsing #
        # ######################### #
        cli = Cli(root)




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

