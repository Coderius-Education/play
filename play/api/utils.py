"""Game functions and utilities."""

import asyncio as _asyncio
import logging as _logging
import os as _os
import threading as _threading

import pygame

from ..callback import callback_manager, CallbackType
from ..core import game_loop as _game_loop
from ..globals import globals_list
from ..io.keypress import keyboard_state
from ..loop import get_loop as _get_loop
from ..physics import set_physics_simulation_steps as _set_physics_simulation_steps
from ..utils import color_name_to_rgb as _color_name_to_rgb

_program_started = False  # pylint: disable=invalid-name
_initial_pid = _os.getpid()  # pylint: disable=invalid-name
_auto_start_thread = None  # pylint: disable=invalid-name


def _auto_start_if_needed():
    """Auto-start the program if the user forgot to call play.start_program().

    Waits for the main thread to finish (i.e. the user's script has fully
    executed) and then calls start_program() if it was never called.
    """
    _threading.main_thread().join()
    if not _program_started:
        try:
            start_program()
        except RuntimeError:
            pass  # start_program() was called just before the main thread ended


def _schedule_auto_start():
    """Schedule an auto-start check. Called when callbacks or sprites are registered."""
    global _auto_start_thread
    if _program_started or _auto_start_thread is not None:
        return
    _auto_start_thread = _threading.Thread(target=_auto_start_if_needed, daemon=False)
    _auto_start_thread.start()


def _cancel_auto_start():
    """Cancel the pending auto-start (called when start_program() is invoked normally)."""
    global _auto_start_thread
    _auto_start_thread = None


callback_manager.on_first_callback = _schedule_auto_start
globals_list.on_first_sprite = _schedule_auto_start


def start_program():
    """
    Calling this function starts your program running.

    play.start_program() should almost certainly go at the very end of your program.
    """
    global _program_started
    if _program_started:
        raise RuntimeError(
            "You've already started the program! Calling play.start_program() "
            "twice can cause errors. Check to make sure it's only called once "
            "at the very bottom of your file."
        )

    _program_started = True
    _cancel_auto_start()
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
