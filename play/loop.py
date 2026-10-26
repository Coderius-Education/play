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

_TASK_NAME_PREFIX = "play: "

if sys.version_info >= (3, 12):
    from asyncio import eager_task_factory as _eager_task_factory
else:
    from play._eager_start_py311 import eager_task_factory as _eager_task_factory

_tasks = set()

_page_exception_handler = None  # pylint: disable=invalid-name


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future") or context.get("task")
    task_name = task.get_name() if hasattr(task, "get_name") else "unknown"
    message = context.get("message", "Unhandled exception in async task")

    if RUNS_IN_BROWSER and not task_name.startswith(_TASK_NAME_PREFIX):
        _pass_to_the_page(the_loop, context)
        return

    if not exception and message.startswith(_DESTROYED_PENDING):
        # Expected once the loop has stopped, and nothing the user can act on.
        play_logger.debug(message)
        return

    if not exception:
        play_logger.critical(message)
    elif globals_list.claim_first_error():
        play_logger.critical(
            "Unhandled exception in task '%s':\n%s",
            task_name,
            "".join(traceback.format_exception(exception)),
        )

    stop_loop()


def _pass_to_the_page(the_loop, context):
    """Hand an error that is not play's to the handler the page had, or to asyncio's default one."""
    if _page_exception_handler is None:
        the_loop.default_exception_handler(context)
    else:
        _page_exception_handler(the_loop, context)


def get_loop():
    """Get or create the global event loop.

    Creates a new loop on first call and after a fork (detected via pid change);
    in the browser it takes the page's loop, which keeps running on its own.
    """
    global _loop, _creator_pid, _page_exception_handler

    pid = os.getpid()
    if _loop is None or _creator_pid != pid:
        if RUNS_IN_BROWSER:
            _loop = asyncio.get_event_loop()
            _page_exception_handler = _loop.get_exception_handler()
        else:
            _loop = asyncio.new_event_loop()
            asyncio.set_event_loop(_loop)
            _loop.set_debug(False)
        _loop.set_exception_handler(_handle_exception)
        _creator_pid = pid
        _tasks.clear()

    return _loop


def _task_name(coro):
    """Return the name of play's task for *coro*."""
    return _TASK_NAME_PREFIX + coro.__qualname__


def create_task(coro):
    """Schedule a coroutine as one of play's tasks; it starts on a later turn of the loop.
    :param coro: The coroutine to run. If the program has stopped, it does not run.
    :return: The task."""
    return _as_play_task(get_loop().create_task(coro, name=_task_name(coro)))


def start_task(coro):
    """Run a coroutine straight away up to its first await, then go on with it as one of play's tasks.
    :param coro: The coroutine to run. If it stops the program before its first await, it goes no further.
    :return: The task."""
    return _as_play_task(_eager_task_factory(get_loop(), coro, name=_task_name(coro)))


def _as_play_task(task):
    """Cancel *task* if the program has stopped; in the browser, keep hold of it until it is done."""
    if globals_list.program_state is ProgramState.STOPPED:
        task.cancel()
    elif RUNS_IN_BROWSER:
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    return task


def stop_loop():
    """Mark the program as stopped and stop the event loop; in the browser, cancel play's tasks."""
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        for task in list(_tasks):
            task.cancel()
    else:
        get_loop().stop()


def _ignore_outcome(task):
    """Take the outcome of an ended task, so the loop does not report it."""
    if not task.cancelled():
        task.exception()


def _end_now(task):
    """Cancel *task* and close its coroutine, so its finally blocks run straight away."""
    task.cancel()
    task.add_done_callback(_ignore_outcome)
    coro = task.get_coro()
    if coro is not None:
        try:
            coro.close()
        except RuntimeError:
            pass


def reset():
    """Stop the program and end play's tasks now; on the desktop, also close play's event loop.
    :raises RuntimeError: On the desktop, when called while the program is running."""
    global _loop, _creator_pid

    if not RUNS_IN_BROWSER and _loop is not None and _loop.is_running():
        raise RuntimeError(
            "play.reset_program() cannot run while the program is running. "
            "Call it after play.start_program() has returned."
        )
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        try:
            current = asyncio.current_task()
        except RuntimeError:
            current = None
        for task in list(_tasks):
            if task is not current:
                _end_now(task)
        _tasks.clear()
        return
    if _loop is None or _loop.is_closed():
        return
    for task in asyncio.all_tasks(_loop):
        _end_now(task)
    _loop.close()
    _loop = None
    _creator_pid = None
