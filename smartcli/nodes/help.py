from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable


#################
# Help Building #
#################

class HelpRoot:

    def __init__(self, root: IHelp):
        self._root: IHelp = root


class HelpManager(HelpRoot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._header = HeaderBuilder(self._root)
        self._synopsis = SynopsisBuilder(self._root)
        self._description = DescriptionBuilder(self._root)
        self._visible_nodes_section = VisibleNodesSectionBuilder(self._root)
        self._hidden_nodes_section = HiddenNodesSectionBuilder(self._root)
        self._parameters_section = ParametersSectionBuilder(self._root)
        self._flags_section = FlagsSectionBuilder(self._root)
        self._content: list = []

    def _build_help(self) -> list:
        self._content += self._header.build()
        self._content += self._description.build()
        self._content += self._visible_nodes_section.build()
        self._content += self._hidden_nodes_section.build()
        self._content += self._flags_section.build()
        self._content += self._parameters_section.build()
        return self._content


class SectionBuilder(ABC):

    def build(self) -> list:
        section = self._build_section()
        if isinstance(section, str):
            section = [section]
        return [self.get_section_name(), list(section)]

    @abstractmethod
    def get_section_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _build_section(self):
        raise NotImplementedError


class HeaderBuilder(HelpRoot, SectionBuilder):

    def get_section_name(self) -> str:
        return 'Name'

    def _build_section(self) -> list:
        return [self._root.get_help_naming_string(),
                self.get_header_description_string()]

    def get_header_description_string(self) -> str:
        return self._root.help.short_description


class SynopsisBuilder(HelpRoot, SectionBuilder):

    def get_section_name(self) -> str:
        return 'Synopsis'

    def _build_section(self):
        return []  # TODO: implement


class DescriptionBuilder(HelpRoot, SectionBuilder):

    def get_section_name(self) -> str:
        return 'Description'

    def _build_section(self):
        return self._root.help.long_description


class SubHelpBuilder(HelpRoot, SectionBuilder, ABC):

    def get_sub_helps(self) -> list[IHelp]:
        sub_helps = self._root.get_sub_helps()
        kind = self.get_section_name()
        if kind in sub_helps:
            return sub_helps[kind]
        return []

    def _build_section(self):
        return list(map(self.build_single_sub_help, self.get_sub_helps()))

    def build_single_sub_help(self, sub_help: IHelp) -> list:
        return [sub_help.get_help_naming_string(), self.build_single_sub_help_description(sub_help)]

    def build_single_sub_help_description(self, sub_help: IHelp) -> list:
        return [sub_help.help.short_description]


class VisibleNodesSectionBuilder(SubHelpBuilder):

    def get_section_name(self) -> str:
        return 'Nodes'


class HiddenNodesSectionBuilder(SubHelpBuilder):

    def get_section_name(self) -> str:
        return 'Hidden Nodes'


class ParametersSectionBuilder(SubHelpBuilder):

    def get_section_name(self) -> str:
        return 'Parameters'


class FlagsSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return 'Flags'


################
# Help storing #
################

class IHelp(ABC):
    '''
    Interface for objects that have help and can be managed by HelpManager
    '''

    @abstractmethod
    def get_help(self) -> Help:
        raise NotImplementedError

    @property
    def help(self):
        return self.get_help()

    @abstractmethod
    def get_sub_helps(self) -> dict[str, list[IHelp]]:
        raise NotImplemented

    @abstractmethod
    def _get_help_naming(self) -> Iterable[str] | str:
        raise NotImplemented

    def get_help_naming_string(self):
        naming = self._root.get_help_naming()
        if isinstance(naming, Iterable):
            naming = str(list(naming))[1:-2]
        return naming


class Help:

    def __init__(self, short_description: str, long_description: str = ''):
        self._short_description = short_description
        self._long_description = long_description

    @property
    def short_description(self):
        return self._short_description

    @property
    def long_description(self):
        return self._long_description
