"""This module is used to create a global event loop for the application."""

import os
import sys
import asyncio
import traceback
from .io.logging import play_logger

_loop = None  # pylint: disable=invalid-name
_creator_pid = None  # pylint: disable=invalid-name


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"

    if exception:
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        tb_str = "".join(tb_lines)
        play_logger.critical("Unhandled exception in task '%s':\n%s", task_name, tb_str)
    else:
        play_logger.critical(
            context.get("message", "Unhandled exception in async task")
        )

    the_loop.stop()


def get_loop():
    """Get or create the global event loop.

    Creates a new loop on first call and after a fork (detected via pid change).
    This ensures module-level imports of play don't break forked processes
    (e.g. pytest --forked).
    """
    global _loop, _creator_pid

    pid = os.getpid()
    if _loop is None or _creator_pid != pid:
        if sys.version_info >= (3, 14):
            asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _loop.set_debug(False)
        _loop.set_exception_handler(_handle_exception)
        _creator_pid = pid

    return _loop
