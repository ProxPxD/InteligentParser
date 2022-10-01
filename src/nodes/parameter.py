from .finalNode import FinalNode, default_param
from .node import Node


class Parameter(FinalNode):

    def __init__(self, name: str, parent: Node, *, limit: int = None, default: default_param = None):
        super().__init__(name, parent, limit=limit if limit is not None else 1, default=default)

    def set_default(self, default: default_param):
        super(Parameter, self).set_default(default)
        if default is not None:
            self._parent._add_optional_parameter(self)
        else:
            self._parent._remove_optional_parameter(self)
