from .nodes.root import Root
from .parserB import ParserB


class Parser:

    def __init__(self):
        root = Root()
        root.add_flag('-m')
        root.add_hidden_node('trans', )

        self._parser = ParserB(root=root)
