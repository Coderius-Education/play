"""This module is used to create a global event loop for the application."""

import os
import sys
import asyncio
import traceback
import types
from play.globals import globals_list, ProgramState
from play.io.logging import play_logger

_loop = None  # pylint: disable=invalid-name
_creator_pid = None  # pylint: disable=invalid-name


_DESTROYED_PENDING = "Task was destroyed but it is pending!"

RUNS_IN_BROWSER = sys.platform == "emscripten"

_TASK_NAME_PREFIX = "play: "

_EAGER_TASKS = sys.version_info >= (3, 12)

_tasks = set()


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"
    message = context.get("message", "Unhandled exception in async task")

    if RUNS_IN_BROWSER and not task_name.startswith(_TASK_NAME_PREFIX):
        the_loop.default_exception_handler(context)
        return

    if not exception and message.startswith(_DESTROYED_PENDING):
        # Expected once the loop has stopped, and nothing the user can act on.
        play_logger.debug(message)
        return

    if not exception:
        play_logger.critical(message)
    elif first_error_to_show():
        play_logger.critical(
            "Unhandled exception in task '%s':\n%s",
            task_name,
            "".join(traceback.format_exception(exception)),
        )

    stop_loop()


def first_error_to_show():
    """Tell whether an error is the program's first, the only one whose traceback is shown.
    :return: True the first time it is called for a program, False after that."""
    if globals_list.error_shown:
        return False
    globals_list.error_shown = True
    return True


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
        _tasks.clear()

    return _loop


@types.coroutine
def _resume(coro, awaiting):
    """Pass on to *coro*, paused at *awaiting*, what its task sends or throws in."""
    try:
        if awaiting is None:
            awaiting = coro.send(None)
        while True:
            try:
                sent = yield awaiting
            except BaseException as thrown:  # pylint: disable=broad-exception-caught
                awaiting = coro.throw(thrown)
            else:
                awaiting = coro.send(sent)
    except StopIteration as stop:
        return stop.value


async def _carry_on(coro, awaiting):
    """Await the rest of a coroutine that already took its first step."""
    return await _resume(coro, awaiting)


def _start_eagerly(coro, name):
    """Run a coroutine up to its first await, then hand the rest to a task."""
    try:
        awaiting = coro.send(None)
    except StopIteration as stop:
        finished = get_loop().create_future()
        finished.set_result(stop.value)
        return finished
    return get_loop().create_task(_carry_on(coro, awaiting), name=name)


def create_task(coro, eager=False):
    """Start a coroutine as one of play's tasks.
    :param coro: The coroutine to run.
    :param eager: Run it straight away up to its first await; if that stops the program, it goes no further.
    :return: The task, or a finished future if an eager coroutine ended at once."""
    name = _TASK_NAME_PREFIX + coro.__qualname__
    if eager and _EAGER_TASKS:
        task = asyncio.eager_task_factory(get_loop(), coro, name=name)
    elif eager:
        task = _start_eagerly(coro, name)
    else:
        task = get_loop().create_task(coro, name=name)
    if eager and globals_list.program_state is ProgramState.STOPPED:
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
