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

    if the_loop is not _loop:
        play_logger.debug(message)
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


def _cancel(task):
    """Cancel *task*, unless an earlier cancel already has it ending."""
    if not task.cancelling():
        task.cancel()


def stop_loop():
    """Mark the program as stopped and stop the event loop; in the browser, cancel play's tasks."""
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        for task in list(_tasks):
            _cancel(task)
    else:
        get_loop().stop()


_SECONDS_TO_END = 1.0

_RESET_INSIDE_THE_PROGRAM = (
    "play.reset_program() cannot run inside a running play program. Call it "
    "after play.start_program() has returned, or in the browser from the page."
)

_RESET_INSIDE_AN_EVENT_LOOP = (
    "On the desktop, play.reset_program() cannot run inside a running event "
    "loop, such as in asyncio.run(). Call it outside the event loop."
)


def _ignore_outcome(task):
    """Take the outcome of an ended task, so the loop does not report it."""
    if not task.cancelled():
        task.exception()


def _close(task):
    """Close the coroutine of a *task* that did not end when it was cancelled, and forget the task."""
    _tasks.discard(task)
    coro = task.get_coro()
    if coro is not None:
        try:
            coro.close()
        except RuntimeError:
            pass


def _runs_inside_the_program():
    """Whether the code running now is one of play's own tasks."""
    try:
        current = asyncio.current_task()
    except RuntimeError:
        return False
    return current is not None and current.get_name().startswith(_TASK_NAME_PREFIX)


def _another_event_loop_runs():
    """Whether an event loop other than play's runs in this thread."""
    try:
        running = asyncio.get_running_loop()
    except RuntimeError:
        return False
    return running is not _loop


def stop_for_reset():
    """Stop the program and cancel play's tasks, for play.reset_program().
    :return: The cancelled tasks, to end with end_tasks() or end_tasks_and_close_the_loop().
    :raises RuntimeError: When called from inside a running play program, or on the desktop
        inside a running event loop."""
    if RUNS_IN_BROWSER:
        if _runs_inside_the_program():
            raise RuntimeError(_RESET_INSIDE_THE_PROGRAM)
    elif _another_event_loop_runs():
        raise RuntimeError(_RESET_INSIDE_AN_EVENT_LOOP)
    elif _loop is not None and _loop.is_running():
        raise RuntimeError(_RESET_INSIDE_THE_PROGRAM)
    globals_list.program_state = ProgramState.STOPPED
    if RUNS_IN_BROWSER:
        tasks = list(_tasks)
    elif _loop is None or _loop.is_closed():
        tasks = []
    else:
        tasks = list(asyncio.all_tasks(_loop))
    tasks = [task for task in tasks if not task.done()]
    for task in tasks:
        _cancel(task)
        task.add_done_callback(_ignore_outcome)
    return tasks


async def end_tasks(tasks):
    """Wait until the cancelled *tasks* have ended, closing those still running after _SECONDS_TO_END."""
    try:
        if tasks:
            await asyncio.wait(tasks, timeout=_SECONDS_TO_END)
    finally:
        _close_leftovers(tasks)


def _close_leftovers(tasks):
    """Close the *tasks* that have not ended, without showing the errors closing them raises."""
    leftovers = [task for task in tasks if not task.done()]
    if leftovers:
        globals_list.claim_first_error()
    for task in leftovers:
        _close(task)


def end_tasks_and_close_the_loop(tasks):
    """On the desktop, run play's loop until the cancelled *tasks* have ended, then close the loop."""
    global _loop

    if _loop is None or _loop.is_closed():
        return
    ending = _loop.create_task(end_tasks(tasks))
    ending.add_done_callback(lambda _: _loop.stop())
    while not ending.done():
        _loop.run_forever()
    _loop.close()
    _loop = None
    asyncio.set_event_loop(None)
