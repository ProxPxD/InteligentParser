from __future__ import annotations

from src.nodes.defaultStorage import DefaultStorage
from src.nodes.flag import Flag
from src.nodes.smartList import SmartList


class NodeCollection(DefaultStorage, SmartList):

    def __init__(self, limit: int = None, *, name=''):
        self.name = name
        SmartList.__init__(self, limit=limit)

    def add_to_add_names(self, *flags: Flag):
        for flag in flags:
            flag.when_active_add_name_to(self)

    def get(self):
        if self:
            return self[0] if len(self) == 1 else SmartList(self)
        return super().get()
