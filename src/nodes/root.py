from src.nodes.flag import Flag
from src.nodes.node import Node


class Root(Node):

    def __init__(self, name: str = 'root'):
        super().__init__(name)

    def add_global_flag(self, main: str | Flag, *alternative_names: str) -> Flag:
        return self.add_flag(main, *alternative_names)

    def get_global_flag(self, name: str) -> Flag:
        return self.get_flag(name)
