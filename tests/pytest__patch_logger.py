from typing import cast
from unittest.mock import Mock
import logging
import pytest

from reverse_patch.patch_logger import PatchLogger

logger = logging.getLogger('some_logger')


class TestPatchLogger:
    def test_patch_logger(self):
        for method_name in ('debug', 'info', 'warning', 'error', 'critical'):
            _orig_method = getattr(logger, method_name)

            with PatchLogger(logger):
                getattr(logger, method_name)('hello %s, %s', 'Bob', 42)
                cast(Mock, getattr(logger, method_name)).assert_called_once_with('hello %s, %s', 'Bob', 42)

            with PatchLogger(logger):
                with pytest.raises(TypeError):
                    getattr(logger, method_name)('hello %s', 'Foo', 1)

            assert not isinstance(getattr(logger, method_name), Mock)

    def test___mock_log_method(self):
        PatchLogger._mock_log_method('hello %s', 'one')
        PatchLogger._mock_log_method('hello %s %s', 'one', 'two')

        with pytest.raises(TypeError):
            PatchLogger._mock_log_method('hello %s')

