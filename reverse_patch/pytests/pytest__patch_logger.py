from typing import cast
from unittest.mock import Mock
import logging
import pytest

from reverse_patch.patch_logger import PatchLogger

logger = logging.getLogger('some_logger')


def test_patch_logger():
    for method_name in ('debug', 'info', 'warning', 'error', 'critical'):
        _orig_method = getattr(logger, method_name)

        with PatchLogger(logger):
            getattr(logger, method_name)('hello %s, %s', 'Bob', 42)
            cast(Mock, getattr(logger, method_name)).assert_called_once_with('hello %s, %s', 'Bob', 42)

        with PatchLogger(logger):
            with pytest.raises(TypeError):
                getattr(logger, method_name)('hello %s', 'Foo', 1)

        assert not isinstance(getattr(logger, method_name), Mock)
