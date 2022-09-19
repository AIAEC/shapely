from enum import Enum
from typing import List, Any, Optional


class EasyEnum(Enum):
    """
    封装一个方便调用的枚举类
    """

    @classmethod
    def enums(cls) -> List[Any]:
        return [enum for enum in cls]

    @classmethod
    def values(cls) -> List[Any]:
        return [enum.value for enum in cls]

    @classmethod
    def is_one_of(cls, enum) -> bool:
        return any(filter(lambda e: e == enum, cls.enums()))

    @classmethod
    def from_val(cls, val) -> Optional[Any]:
        for enum in cls:
            if enum.value == val:
                return enum

        return None
