from enum import Enum

class Visibility(Enum):
    PUBLIC=1
    PRIVATE=2

    @classmethod
    def choices(cls):
        return [(role.value,role.name.capitalize()) for role in cls]



