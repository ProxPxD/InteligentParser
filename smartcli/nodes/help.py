from __future__ import annotations

import operator as op
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import reduce
from itertools import accumulate
from typing import Iterable

from more_itertools import split_when


#################
# Help Building #
#################


class HelpRoot:

    def __init__(self, root: IHelp, **kwargs):
        super().__init__(**kwargs)
        self._root: IHelp = root


class HelpManager(HelpRoot):

    def __init__(self, root: IHelp, **kwargs):
        super().__init__(root=root, **kwargs)
        self._formatter = HelpFormatter()
        sections = [HeaderBuilder,
                    SynopsisBuilder,
                    DescriptionBuilder,
                    ParametersSectionBuilder,
                    FlagsSectionBuilder,
                    VisibleNodesSectionBuilder,
                    HiddenNodesSectionBuilder,
        ]
        self._sections = list(map(lambda s: s(self._root), sections))

    def print_help(self, out=print) -> None:
        out(self.create_help_string())

    def create_help_string(self) -> str:
        content = self._build_help_content()
        help_string = self._formatter.format(content)
        return help_string

    def _build_help_content(self) -> list:
        is_content_empty = lambda section: section[1] and section[1][0]
        built = map(SectionBuilder.build, self._sections)
        not_empty = filter(is_content_empty, built)
        joined = reduce(op.add, not_empty)
        return joined


class HelpFormatter:

    def __init__(self):
        self._space = ' '
        self._big_space_width = 5
        self._small_space_width = 3
        self._max_width = 120
        self._section_separator = '\n'
        self._option_separator = '\n'

    def format(self, to_format: list | str, depth=0) -> str:
        if isinstance(to_format, list):
            return self._format_list(to_format, depth+1)
        elif isinstance(to_format, str):
            return self._format_long_text(to_format, depth)

        raise ValueError

    def _format_list(self, to_format: list, depth: int) -> str:
        sep = self._get_section_separator(depth)
        prelist = [i-1 for i, elem in enumerate(to_format) if isinstance(elem, list) and elem[0]]
        add_colon_if_is_header = lambda i, part: part + ':' if i in prelist and isinstance(part, str) else part
        not_empty_formatted = (self.format(add_colon_if_is_header(i, part), depth) for i, part in enumerate(to_format) if part and part[0])
        merged = self._lines_to_str(list(not_empty_formatted), sep)
        return merged

    def _format_long_text(self, to_format: str, depth: int) -> str:
        paragraphs = to_format.split('\n')
        formatted = map(lambda p: self._format_paragraph(p, depth), paragraphs)
        return '\n'.join(list(formatted))

    def _format_paragraph(self, paragraph: str, depth: int) -> str:
        if not paragraph:
            return ''
        space_length = self._get_space_length(depth)
        line_max = self._max_width - space_length
        mod_max = lambda a: a // line_max
        is_line_bound = lambda p1, p2: mod_max(p1[0]) != mod_max(p2[0])
        indent = ' ' * space_length

        words = paragraph.split(' ')
        lens_words = map(lambda w: (len(w) + 1, w), words)  # +1 for space
        with_position = accumulate(lens_words, lambda acc, elem: (acc[0] + elem[0], elem[1]))
        lens_lines = split_when(with_position, is_line_bound)
        lines = map(lambda line: ' '.join(list(map(lambda pair: pair[1], line))), lens_lines)
        indented_lines = map(lambda line: indent + line, lines)
        return '\n'.join(list(indented_lines))

    def _lines_to_str(self, lines: list, sep='\n'):
        length = len(lines)
        if length > 1:
            return sep.join(lines)
        if length > 0:
            return lines[0]
        return ''

    def _get_space_length(self, depth: int):
        big, small = self._big_space_width, self._small_space_width
        if depth <= 1:
            return 0
        return big + (small * (depth-2))

    def _get_section_separator(self, depth: int):
        if depth == 2:
            return self._section_separator
        return self._option_separator


class SectionBuilder(HelpRoot, ABC):

    def __init__(self, root, **kwargs):
        super().__init__(root=root, **kwargs)

    def build(self) -> list:
        section = self._build_section()
        if isinstance(section, str):
            section = [section]
        return [self.get_section_name().upper(), list(section)]

    def _get_sub_helps(self, kind: HelpType = None) -> dict[HelpType, list[IHelp]] | list[IHelp]:
        sub_helps = self._root.get_sub_helps()
        if kind is None:
            return sub_helps
        return sub_helps[kind] if kind in sub_helps else []

    def _get_visible_nodes(self) -> list:
        return self._get_sub_helps(HelpType.NODE)

    def _get_hidden_nodes(self) -> list:
        return self._get_sub_helps(HelpType.HIDDEN_NODES)

    def _get_flags(self) -> list:
        return self._get_sub_helps(HelpType.FLAG)

    def _get_parameters(self) -> list:
        return self._get_sub_helps(HelpType.PARAMETER)

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
        return [f'{self._root.get_help_naming_string()} - {self.get_header_description_string()}']

    def get_header_description_string(self) -> str:
        return self._root.help.short_description


class SynopsisBuilder(SectionBuilder):

    def get_section_name(self) -> str:
        return 'Synopsis'

    def _build_section(self):
        return [self._root.help.synopsis or self._build_synopsis()]  # TODO: implement

    def _build_synopsis(self) -> str:
        return ''


class DescriptionBuilder(SectionBuilder):

    def get_section_name(self) -> str:
        return 'Description'

    def _build_section(self):
        return self._root.help.long_description


class SubHelpBuilder(SectionBuilder, ABC):

    def get_sub_helps(self) -> list[IHelp]:
        sub_helps = self._root.get_sub_helps()
        name = self.get_section_name()
        kind = HelpType(name)
        if kind in sub_helps:
            return sub_helps[kind]
        return []

    def _build_section(self):
        return reduce(op.add, map(self.build_single_sub_help, self.get_sub_helps()), [])

    def build_single_sub_help(self, sub_help: IHelp) -> list:
        return [sub_help.get_help_naming_string(), [self.build_single_sub_help_description(sub_help)]]

    def build_single_sub_help_description(self, sub_help: IHelp) -> str:
        return sub_help.help.short_description


class ParametersSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.PARAMETER.value


class VisibleNodesSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.NODE.value


class HiddenNodesSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.HIDDEN_NODES.value


class FlagsSectionBuilder(SubHelpBuilder):
    def get_section_name(self) -> str:
        return HelpType.FLAG.value


class HelpType(Enum):
    NODE = 'Nodes'
    HIDDEN_NODES = 'Hidden Nodes'
    PARAMETER = 'Parameters'
    FLAG = 'Flags'

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

    def _get_help_naming(self) -> Iterable[str] | str:
        raise NameError

    def get_help_naming_string(self):
        naming = self.help.name or self._get_help_naming()
        if not isinstance(naming, str):
            naming = str(list(naming))[1:-2]
        return naming


@dataclass
class Help:
    name: str = ''
    short_description: str = ''
    long_description: str = ''
    synopsis: str = ''
