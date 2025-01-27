from typing import cast, TypeVar, Union
from unittest.mock import MagicMock

__all__ = (
    'm',
)

T = TypeVar('T')


def m(value: T) -> Union[MagicMock, T]:
    """
    casts value to MagicMock type

    ```py
    my_variable = 'hello'

    m(my_variable).assert_called_once_with()  # completion will work like MagicMock
    m(my_variable).startswith()  # completion will work with original type of value
    ```
    """
    return cast(MagicMock, value)
