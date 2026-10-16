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

TASK_NAME_PREFIX = "play: "

_tasks = set()


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"
    message = context.get("message", "Unhandled exception in async task")

    if RUNS_IN_BROWSER and not task_name.startswith(TASK_NAME_PREFIX):
        the_loop.default_exception_handler(context)
        return

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
        _tasks.clear()

    return _loop


class _CarryOn:  # pylint: disable=too-few-public-methods
    """Carry on, in a task, with a coroutine that already ran up to its first await."""

    def __init__(self, coro, awaiting):
        self._coro = coro
        self._awaiting = awaiting

    def __await__(self):
        awaiting = self._awaiting
        if awaiting is None:
            try:
                awaiting = self._coro.send(None)
            except StopIteration as stop:
                return stop.value
        while True:
            try:
                sent = yield awaiting
            except BaseException as thrown:  # pylint: disable=broad-exception-caught
                step = self._coro.throw
                value = thrown
            else:
                step = self._coro.send
                value = sent
            try:
                awaiting = step(value)
            except StopIteration as stop:
                return stop.value


async def _carry_on(coro, awaiting):
    """Await the rest of a coroutine that already took its first step."""
    return await _CarryOn(coro, awaiting)


def _start_eagerly(coro, name):
    """Run a coroutine up to its first await, then hand the rest to a task, or return None if it is done."""
    try:
        awaiting = coro.send(None)
    except StopIteration:
        return None
    if globals_list.program_state is ProgramState.STOPPED:
        coro.close()
        return None
    return get_loop().create_task(_carry_on(coro, awaiting), name=name)


def create_task(coro, eager=False):
    """Start a coroutine as one of play's tasks.
    :param coro: The coroutine to run.
    :param eager: Run it straight away up to its first await.
    :return: The task, or None if an eager coroutine finished straight away."""
    name = TASK_NAME_PREFIX + coro.__qualname__
    if eager and sys.version_info >= (3, 12):
        task = asyncio.eager_task_factory(get_loop(), coro, name=name)
    elif eager:
        task = _start_eagerly(coro, name)
    else:
        task = get_loop().create_task(coro, name=name)
    if task is not None and RUNS_IN_BROWSER:
        _tasks.add(task)
        task.add_done_callback(_tasks.discard)
    return task


def stop_loop(loop=None):
    """Mark the program as stopped and stop the event loop; in the browser, cancel play's tasks."""
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        running = asyncio.current_task(get_loop())
        if running is not None and running.get_name().startswith(TASK_NAME_PREFIX):
            _tasks.add(running)
        for task in list(_tasks):
            task.cancel()
    else:
        (loop if loop is not None else get_loop()).stop()
