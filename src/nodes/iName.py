class IName:

    def __init__(self, name: str = ''):
        self._name = name

    @property
    def name(self):
        return self._name

    def has_name(self, name: str):
        return name == self.name

    def __str__(self):
        return self._name or self.__class__.__name__
