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

_HAS_EAGER_TASK_FACTORY = sys.version_info >= (3, 12)

_tasks = set()


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if isinstance(task, asyncio.Task) else "unknown"
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
    elif globals_list.claim_first_error():
        play_logger.critical(
            "Unhandled exception in task '%s':\n%s",
            task_name,
            "".join(traceback.format_exception(exception)),
        )

    stop_loop()


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
def _relay(coro, awaiting):
    """Relay to *coro*, paused at *awaiting* (None after a bare yield), what its task sends or throws in."""
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
    return await _relay(coro, awaiting)


def _finished(result=None, error=None):
    """Return a future that is already done with *result*, or with *error* if given."""
    future = get_loop().create_future()
    if error is None:
        future.set_result(result)
    else:
        future.set_exception(error)
    return future


def _start_by_hand(coro, name):
    """Run a coroutine up to its first await, then hand the rest to a task."""
    try:
        awaiting = coro.send(None)
    except StopIteration as stop:
        return _finished(result=stop.value)
    except Exception as error:  # pylint: disable=broad-exception-caught
        return _finished(error=error)
    return get_loop().create_task(_carry_on(coro, awaiting), name=name)


def _task_name(coro):
    """Return the name of play's task for *coro*."""
    return _TASK_NAME_PREFIX + coro.__qualname__


def _track(task):
    """Remember one of play's tasks in the browser, so that stopping the program can cancel it."""
    if RUNS_IN_BROWSER:
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    return task


def create_task(coro):
    """Schedule a coroutine as one of play's tasks; it starts on a later turn of the loop.
    :param coro: The coroutine to run.
    :return: The task."""
    return _track(get_loop().create_task(coro, name=_task_name(coro)))


def start_task(coro):
    """Run a coroutine straight away up to its first await, then go on with it as one of play's tasks.
    :param coro: The coroutine to run. If it stops the program before its first await, it goes no further.
    :return: The task, or a finished future if the coroutine ended or failed before its first await.
    """
    if _HAS_EAGER_TASK_FACTORY:
        task = asyncio.eager_task_factory(get_loop(), coro, name=_task_name(coro))
    else:
        task = _start_by_hand(coro, _task_name(coro))
    if globals_list.program_state is ProgramState.STOPPED:
        task.cancel()
        return task
    return _track(task)


def stop_loop():
    """Mark the program as stopped and stop the event loop; in the browser, cancel play's tasks."""
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        for task in list(_tasks):
            task.cancel()
    else:
        get_loop().stop()
