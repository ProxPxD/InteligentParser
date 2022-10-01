from __future__ import annotations

from typing import Type


class AbstractNode:

    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def _add_any_node(self, to_add: str | AbstractNode, collection: dict[str, AbstractNode], my_class: Type[AbstractNode]):
        node = self._get_node_if_string(to_add, my_class)
        if node.name in collection:
            type_name = my_class.__class__.__name__.__str__()
            raise ValueError(f'{type_name + " " if type_name else ""}{node.name} already exists in node {self._name}')

        collection[node.name] = node
        return node

    def _get_node_if_string(self, node: str | AbstractNode, my_class: Type[AbstractNode]) -> AbstractNode:
        if isinstance(node, str):
            node = my_class(node)
        if not isinstance(node, AbstractNode):
            raise TypeError(f'Cannot add {type(node)} as a {my_class.__class__.__name__.__str__()}')

        return node

    def _get_save(self, name: str, from_dict: dict[str, AbstractNode]) -> AbstractNode:
        if name not in from_dict:
            raise ValueError(f'Name {name} does not belong to {self.name}')
        return from_dict[name]