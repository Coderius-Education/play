"""This module is used to create a global event loop for the application."""

import os
import asyncio
import traceback
from .globals import globals_list, ProgramState
from .io.logging import play_logger

_loop = None  # pylint: disable=invalid-name
_creator_pid = None  # pylint: disable=invalid-name


_DESTROYED_PENDING = "Task was destroyed but it is pending!"


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"
    message = context.get("message", "Unhandled exception in async task")

    if not exception and message.startswith(_DESTROYED_PENDING):
        # Expected once the loop has stopped, and nothing the user can act on.
        play_logger.debug(message)
        return

    if exception:
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        tb_str = "".join(tb_lines)
        play_logger.critical("Unhandled exception in task '%s':\n%s", task_name, tb_str)
    else:
        play_logger.critical(message)

    globals_list.program_state = ProgramState.STOPPED
    the_loop.stop()


def get_loop():
    """Get or create the global event loop.

    Creates a new loop on first call and after a fork (detected via pid change).
    """
    global _loop, _creator_pid

    pid = os.getpid()
    if _loop is None or _creator_pid != pid:
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)
        _loop.set_debug(False)
        _loop.set_exception_handler(_handle_exception)
        _creator_pid = pid

    return _loop


def stop_loop():
    """Stop the event loop and mark the program as stopped.

    start_program() only runs the loop on while the program is not stopped,
    so a stop that is not marked here leaves it waiting on an empty loop.
    """
    globals_list.program_state = ProgramState.STOPPED
    get_loop().stop()
