"""
This module contains helper functions for running callback functions.
"""

import inspect
import traceback

from play.io.logging import play_logger
from play.loop import (
    create_task as _create_task,
    first_error_to_show as _first_error_to_show,
    stop_loop as _stop_loop,
)
from play.utils.async_helpers import make_async


def run_callback(callback, required_args, optional_args, *args, **kwargs):
    """Schedule a callback as a fire-and-forget task.

    This is a convenience alias for :func:`fire_async_callback`.
    """
    fire_async_callback(callback, required_args, optional_args, *args, **kwargs)


def _positional_parameters(func):
    """Return the names of the positional parameters of *func*, leaving out a bound self."""
    return [
        parameter.name
        for parameter in inspect.signature(func).parameters.values()
        if parameter.kind
        in (parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD)
    ]


def _resolve_callback_args(callback, required_args, optional_args, *args):
    """Resolve the arguments for a callback, respecting original_function wrappers.

    Returns the (actual_cb, callback_args) tuple, or raises ValueError if the
    callback signature doesn't match.
    """
    if not inspect.iscoroutinefunction(callback):
        raise ValueError("The callback function must be an async function.")
    actual_cb = callback
    if hasattr(callback, "original_function"):
        actual_cb = callback.original_function
    actual_args = _positional_parameters(actual_cb)
    if (
        len(required_args)
        <= len(actual_args)
        <= len(required_args) + len(optional_args)
    ):
        return actual_cb, args[: len(actual_args)]
    if len(required_args) == 0:
        raise ValueError(
            f"The callback function must not take in any arguments.\n"
            f"On line {actual_cb.__code__.co_firstlineno} in {actual_cb.__code__.co_filename}"
        )
    raise ValueError(
        f"The callback function must take in {len(required_args)} argument(s):\n"
        f"Required: {required_args}\n"
        f"{len(optional_args)} optional argument(s): {optional_args}\n"
        f"On line {actual_cb.__code__.co_firstlineno} in {actual_cb.__code__.co_filename}"
    )


async def run_async_callback(callback, required_args, optional_args, *args, **kwargs):
    """
    Run a callback function with the given arguments.
    :param callback: The callback function to run.
    :param required_args: The required arguments for the callback function.
    :param optional_args: The optional arguments for the callback function.
    :param args: The arguments to pass to the callback function.
    :param kwargs: The keyword arguments to pass to the callback
    :return: The result of the callback function.
    """
    _, callback_args = _resolve_callback_args(
        callback, required_args, optional_args, *args
    )
    await callback(*callback_args, **kwargs)


def _show_first_error(exc):
    """Stop the program and print the traceback, for the first error only."""
    if not _first_error_to_show():
        return
    _stop_loop()
    traceback.print_exception(type(exc), exc, exc.__traceback__)
    play_logger.critical("Error in callback task: %s", exc)


async def _stop_on_error(callback, args, kwargs):
    """Run a callback task, showing its error as soon as it is raised."""
    try:
        await callback(*args, **kwargs)
    except Exception as exc:  # pylint: disable=broad-exception-caught
        _show_first_error(exc)


def contact_callback(func, *args, contact, running, optional_args=()):
    """Wrap a callback for a contact that begins or ends.
    :param func: The function to run. A plain function runs straight away; an async
        one starts straight away as a task of its own, so its awaits do not hold up
        the game, and is skipped while its previous run for this contact has not finished.
    :param args: The arguments to offer to func.
    :param contact: What tells this contact apart, such as ``(other_sprite, True)`` for one that begins.
    :param running: The set of contacts whose async run has not finished.
    :param optional_args: The names of the arguments func may leave out.
    :return: An async function without arguments that runs or starts func."""
    async_func = make_async(func)

    async def run():
        await run_async_callback(async_func, [], list(optional_args), *args)

    if not inspect.iscoroutinefunction(func):
        return run

    key = (func, *contact)

    async def start():
        if key not in running:
            running.add(key)
            _create_task(
                _stop_on_error(_one_at_a_time, (run, key, running), {}), eager=True
            )

    return start


async def _one_at_a_time(run, key, running):
    """Await *run*, then let the contact *key* start again."""
    try:
        await run()
    finally:
        running.discard(key)


def fire_async_callback(callback, required_args, optional_args, *args, **kwargs):
    """Like run_async_callback but schedules the callback as a task (fire-and-forget).

    Use this for event callbacks (key press, mouse click, etc.) that should not
    block the game loop when they contain awaits like play.timer().
    """
    _, callback_args = _resolve_callback_args(
        callback, required_args, optional_args, *args
    )
    _create_task(_stop_on_error(callback, callback_args, kwargs))


async def run_any_async_callback(callbacks, *args, **kwargs):
    """
    Run a callback function with the given arguments.
    :param callbacks: A list of callback functions to run.
    :param args: The arguments to pass to the callback function.
    :param kwargs: The keyword arguments to pass to the callback
    :return: The result of the callback function.
    """
    if not isinstance(callbacks, list):
        raise ValueError("The callbacks parameter must be a list of async functions.")

    for callback in callbacks:
        if callable(callback):
            await run_async_callback(callback, [], [], *args, **kwargs)
