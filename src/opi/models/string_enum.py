from enum import StrEnum
from typing import cast

__all__ = [
    "StringEnum",
]


class StringEnum(StrEnum):
    """
    Variant of StrEnum that allows case-insensitive conversion of a plain string into the corresponding Enum member.
    """

    @classmethod
    def _missing_(cls, value: object, /) -> "StringEnum":
        try:
            # > Any value that can be cast into a string is supported.
            value = str(value)
        except (TypeError, ValueError):
            raise TypeError(f"Value {value} cannot be converted to {cls.__name__}")

        members = cls._member_map_
        for member_name in members.keys():
            if member_name.casefold() == value.casefold():
                return cast(StringEnum, members[member_name])
        # > No suitable member found
        raise ValueError(f"Unknown Enum member: {value}")
