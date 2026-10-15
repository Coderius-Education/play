"""This module is used to create a global event loop for the application."""

import os
import sys
import asyncio
import traceback
from play.globals import globals_list, ProgramState
from play.io.logging import play_logger

_loop = None  # pylint: disable=invalid-name
_creator_pid = None  # pylint: disable=invalid-name


_DESTROYED_PENDING = "Task was destroyed but it is pending!"

RUNS_IN_BROWSER = sys.platform == "emscripten"


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"
    message = context.get("message", "Unhandled exception in async task")

    if not exception and message.startswith(_DESTROYED_PENDING):
        # Expected once the loop has stopped, and nothing the user can act on.
        play_logger.debug(message)
        return

    if exception and globals_list.error_shown:
        stop_loop(the_loop)
        return

    if exception:
        globals_list.error_shown = True
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        tb_str = "".join(tb_lines)
        play_logger.critical("Unhandled exception in task '%s':\n%s", task_name, tb_str)
    else:
        play_logger.critical(message)

    stop_loop(the_loop)


def get_loop():
    """Get or create the global event loop.

    Creates a new loop on first call and after a fork (detected via pid change);
    in the browser it takes the page's loop, which keeps running on its own.
    """
    global _loop, _creator_pid

    pid = os.getpid()
    if _loop is None or _creator_pid != pid:
        if RUNS_IN_BROWSER:
            _loop = asyncio.get_event_loop()
        else:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            _loop.set_debug(False)
        _loop.set_exception_handler(_handle_exception)
        _creator_pid = pid

    return _loop


def stop_loop(loop=None):
    """Mark the program as stopped and stop the event loop, unless it is the page's."""
    globals_list.program_state = ProgramState.STOPPED
    if not RUNS_IN_BROWSER:
        (loop if loop is not None else get_loop()).stop()
