"""Game functions and utilities."""  # pylint: disable=cyclic-import

import asyncio as _asyncio
import logging as _logging
import os as _os
import sys as _sys

import pygame

from ..callback import callback_manager, CallbackType
from ..core import game_loop as _game_loop
from ..globals import globals_list
from ..io.keypress import keyboard_state
from ..loop import get_loop as _get_loop
from ..physics import set_physics_simulation_steps as _set_physics_simulation_steps
from ..utils import color_name_to_rgb as _color_name_to_rgb, run_once as _run_once

_program_started = False  # pylint: disable=invalid-name
_initial_pid = _os.getpid()  # pylint: disable=invalid-name
_should_auto_start = False  # pylint: disable=invalid-name


def _make_main_return_trace(existing_trace, existing_f_trace):
    """Create a frame-trace function for the __main__ frame.

    Fires start_program() when the frame returns, then restores the previous
    global trace. Wraps any existing frame trace so debuggers/coverage survive.
    """

    def _on_main_return(_frame, event, _arg):  # pylint: disable=unused-argument
        if event == "return":
            if _should_auto_start and not _program_started:
                try:
                    start_program()
                except RuntimeError as exc:
                    if "already started" not in str(exc):
                        raise
            if existing_trace is None:
                _sys.settrace(None)
            if existing_f_trace is not None:
                existing_f_trace(_frame, event, _arg)
            return None  # CPython ignores the return value on 'return' events
        if event == "exception":
            if existing_trace is None:
                _sys.settrace(None)
            if existing_f_trace is not None:
                return existing_f_trace(_frame, event, _arg)
            return None
        # Return value of existing_f_trace is intentionally discarded: we
        # always keep _on_main_return as the local trace so we can detect
        # the 'return' event.  In practice, coverage tools (e.g. pytest-cov)
        # return themselves, so they are not disrupted.
        if existing_f_trace is not None:
            existing_f_trace(_frame, event, _arg)
        return _on_main_return

    return _on_main_return


@_run_once
def _schedule_auto_start():
    """Set up auto-start when the user's script finishes.

    Walks the call stack to find the __main__ frame and installs a trace
    that fires start_program() when that frame returns. This runs on the
    main thread before interpreter shutdown — required for pygame on Windows.

    Preserves any existing sys.settrace (debuggers, coverage, etc.) by
    wrapping the frame trace instead of replacing the global trace.
    """
    global _should_auto_start  # pylint: disable=global-statement
    _should_auto_start = True

    # CPython-specific: _getframe() is an implementation detail but fine here
    # since pygame targets CPython.
    frame = _sys._getframe()  # pylint: disable=protected-access
    while frame is not None:
        if frame.f_globals.get("__name__") == "__main__":
            existing_trace = _sys.gettrace()
            if existing_trace is None:
                _sys.settrace(lambda *_args: None)
            frame.f_trace = _make_main_return_trace(existing_trace, frame.f_trace)
            frame.f_trace_lines = False
            break
        frame = frame.f_back
    # If no __main__ frame was found (e.g. interactive REPL, embedded context),
    # _should_auto_start is True but no trace is installed — start_program()
    # won't fire automatically and the user must call it explicitly.


callback_manager.on_first_callback = _schedule_auto_start


def _cleanup_auto_start():
    """Reset all auto-start state and remove any installed frame trace.

    Used by test fixtures to prevent state leakage between tests.
    """
    global _program_started, _should_auto_start  # pylint: disable=global-statement
    _program_started = False
    _should_auto_start = False
    _schedule_auto_start.has_run = False
    callback_manager.on_first_callback = _schedule_auto_start

    frame = _sys._getframe()  # pylint: disable=protected-access
    while frame is not None:
        if frame.f_globals.get("__name__") == "__main__":
            frame.f_trace = None
            break
        frame = frame.f_back


def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    global _program_started, _should_auto_start  # pylint: disable=global-statement
    if _program_started:
        raise RuntimeError(
            "You've already started the program! Calling play.start_program() "
            "twice can cause errors. Check to make sure it's only called once "
            "at the very bottom of your file."
        )

    _program_started = True
    _should_auto_start = False
    callback_manager.run_callbacks(CallbackType.WHEN_PROGRAM_START)

    _get_loop().create_task(_game_loop())
    try:
        _get_loop().run_forever()
    finally:
        logger = _logging.getLogger("asyncio")
        logger.setLevel(_logging.CRITICAL)
        if _os.getpid() == _initial_pid:
            pygame.quit()


def stop_program():
    """
    Calling this function stops your program running.

    play.stop_program() should almost certainly go at the very end of your program.
    """
    _get_loop().stop()
    if _os.getpid() == _initial_pid:
        pygame.display.quit()
        pygame.quit()


async def animate():
    """
    Wait for the next frame to be drawn.
    """
    await _asyncio.sleep(0)


def set_backdrop(color):
    """Set the backdrop color or image for the game.
    :param color: The color or image to set as the backdrop.
    """
    globals_list.backdrop = _color_name_to_rgb(color)
    globals_list.backdrop_type = "color"


def set_backdrop_image(image):
    """Set the backdrop image for the game.
    :param image: The image to set as the backdrop.
    """
    globals_list.backdrop = pygame.image.load(image)
    globals_list.backdrop_type = "image"


async def timer(seconds=1.0):
    """Wait a number of seconds. Used with the await keyword like this:
    :param seconds: The number of seconds to wait.
    :return: True after the number of seconds has passed.
    """
    await _asyncio.sleep(seconds)
    return True


def key_is_pressed(*keys):
    """
    Returns True if any of the given keys are pressed.

    Example:

        @play.repeat_forever
        async def do():
            if play.key_is_pressed('up', 'w'):
                print('up or w pressed')
    """
    for key in keys:
        if key in keyboard_state.pressed:
            return True
    return False


def set_physics_simulation_steps(num_steps: int) -> None:
    """
    Set the number of simulation steps for the physics engine.
    :param num_steps: The number of simulation steps.
    """
    _set_physics_simulation_steps(num_steps)
