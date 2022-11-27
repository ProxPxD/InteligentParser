from __future__ import annotations

import operator as op
from abc import ABC, abstractmethod
from enum import Enum
from functools import reduce
from typing import Iterable

from more_itertools import chunked


class HelpType(Enum):
    NODE = 'Nodes'
    HIDDEN_NODES = 'Hidden Nodes'
    PARAMETER = 'Parameters'
    FLAG = 'Flags'

#################
# Help Building #
#################


class HelpRoot:

    def __init__(self, root: IHelp):
        self._root: IHelp = root


class HelpManager(HelpRoot):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._formatter = HelpFormatter()
        sections = [HeaderBuilder,
                    SynopsisBuilder,
                    DescriptionBuilder,
                    ParametersSectionBuilder,
                    FlagsSectionBuilder,
                    VisibleNodesSectionBuilder,
                    HiddenNodesSectionBuilder,
                    ParametersSectionBuilder,
        ]
        self._sections = list(map(lambda s: s(self._root), sections))

    def create_help_string(self):
        content = self._build_help_content()
        help_string = self._formatter.format(content)
        return help_string

    def _build_help_content(self) -> list:
        self._content = list(reduce(op.add, map(SectionBuilder.build, self._sections)))
        return self._content


class HelpFormatter:

    def __init__(self):
        self._space = ' '
        self._big_space_width = 7
        self._small_space_width = 3
        self._max_width = 1000
        self._section_separator = '\n\n'
        self._option_separator = '\n\n'

    def format(self, to_format: list | str, depth=0) -> str:
        if isinstance(to_format, list):
            return self._format_list(to_format, depth+1)
        elif isinstance(to_format, str):
            return self._format_str(to_format, depth)

        raise ValueError

    def _format_list(self, to_format: list, depth: int) -> str:
        sep = self._get_section_separator(depth)
        more_depth = depth + 1
        formatted = map(lambda part: self.format(part, more_depth), to_format)
        merged = reduce(lambda a, b: f'{a}{sep}{b}', formatted)
        return merged

    def _format_str(self, to_format: str, depth: int) -> str:
        space_length = self._get_space_length(depth)
        text_length = self._max_width - space_length
        lines = map(''.join, chunked(to_format, text_length))
        indent = self._space * space_length
        indented_lines = map(lambda line: indent + line, lines)
        return '\n'.join(indented_lines)

    def _get_space_length(self, depth: int):
        big, small = self._big_space_width, self._small_space_width
        return big + (small * (depth-1))

    def _get_section_separator(self, depth: int):
        if depth == 0:
            return self._section_separator
        return self._option_separator


class SectionBuilder(HelpRoot, ABC):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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


class HeaderBuilder(SectionBuilder):

    def get_section_name(self) -> str:
        return 'Name'

    def _build_section(self) -> list:
        return [self._root.get_help_naming_string(),
                self.get_header_description_string()]

    def get_header_description_string(self) -> str:
        return self._root.help.short_description


class SynopsisBuilder(SectionBuilder):

    def get_section_name(self) -> str:
        return 'Synopsis'

    def _build_section(self):
        return []  # TODO: implement


class DescriptionBuilder(SectionBuilder):

    def get_section_name(self) -> str:
        return 'Description'

    def _build_section(self):
        return self._root.help.long_description


class SubHelpBuilder(SectionBuilder, ABC):

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


class ParametersSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.PARAMETER.name


class VisibleNodesSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.NODE.name


class HiddenNodesSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.HIDDEN_NODES.name


class FlagsSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.FLAG.name


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
    def get_sub_helps(self) -> dict[HelpType, list[IHelp]]:
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
