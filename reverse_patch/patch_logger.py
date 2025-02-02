import logging
from unittest.mock import patch

__all__ = (
    'PatchLogger',
)


class PatchLogger:
    """
    This context manager patches `debug`, `info`, `warning` and `critical` method of the logger.
    It adds a side_effect to created mock objects.
    The side_effect will check that passed arguments in calls of logger methods match its message template.

    Usage:
    ```py
    import logging
    from reverse_patch.patch_logger import PatchLogger

    logger = logging.getLogger('my_logger')

    class TestSomething:
        def test_something(self):
            with
    ```
    """
    def __init__(self, logger: logging.Logger):
        self._logger: logging.Logger = logger
        self._patchers = []

        for method_name in ('debug', 'info', 'error', 'warning', 'critical'):
            self._patchers.append(patch.object(self._logger, method_name, side_effect=self._mock_log_method))

    # noinspection PyUnusedLocal
    @staticmethod
    def _mock_log_method(msg, *args, **kwargs):
        msg % tuple(arg for arg in args)

    def __enter__(self) -> 'PatchLogger':
        for patcher in self._patchers:
            patcher.__enter__()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for patcher in reversed(self._patchers):
            patcher.__exit__(None, None, None)
