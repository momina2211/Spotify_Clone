from enum import Enum

class RoleEnum(Enum):
    USER = 1
    ARTIST = 2

    @classmethod
    def choices(cls):
        return [(role.value,role.name.capitalize()) for role in cls]