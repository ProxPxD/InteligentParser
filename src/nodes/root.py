from .flag import Flag
from .node import Node


class Root(Node):

    def __init__(self, name: str = 'root'):
        super().__init__(name)

    def add_global_flag(self, to_add: str | Flag):
        return self.add_flag(to_add)

    def get_global_flag(self, name: str):
        return self.get_flag(name)
