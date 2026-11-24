"""This module contains the Mouse class and the mouse object."""

import math as _math

from play.callback import callback_manager, CallbackType
from play.utils.async_helpers import make_async
from play.objects.sprite import point_touching_sprite
from play.callback.callback_helpers import run_async_callback


class Mouse:
    def __init__(self):
        self.x = 0
        self.y = 0
        self._is_clicked = False

    @property
    def is_clicked(self):
        """Return whether the mouse is clicked.
        :return: True if the mouse is clicked, False otherwise."""
        return self._is_clicked

    def is_touching(self, other):
        """Check if the mouse is touching a sprite.
        :param other: The sprite to check.
        :return: True if the mouse is touching the sprite, False otherwise."""
        return point_touching_sprite((self.x, self.y), other)

    # @decorator
    def when_clicked(self, *buttons):
        """Run a function when the mouse is clicked, by any button or only the named ones.
        :param buttons: The function to run, or 'left', 'middle', 'right', 'back' or 'forward'; a list: held together.
        :return: The function, or a decorator when buttons are named."""
        if _is_a_single_function(buttons):
            return _when_any_button(CallbackType.WHEN_CLICKED, buttons[0])
        return _when_buttons(CallbackType.WHEN_CLICKED, buttons)

    # @decorator
    def when_click_released(self, *buttons):
        """Run a function when the mouse click is released, by any button or only the named ones.
        :param buttons: The function to run, or 'left', 'middle', 'right', 'back' or 'forward'; a list: held together.
        :return: The function, or a decorator when buttons are named."""
        if _is_a_single_function(buttons):
            return _when_any_button(CallbackType.WHEN_CLICK_RELEASED, buttons[0])
        return _when_buttons(CallbackType.WHEN_CLICK_RELEASED, buttons)

    # @decorator
    def while_pressed(self, *buttons):
        """Run a function every frame while a mouse button, or one of the named ones, is held down.
        :param buttons: The function to run, or 'left', 'middle', 'right', 'back' or 'forward'; a list: held together.
        :return: The function, or a decorator when buttons are named."""
        if _is_a_single_function(buttons):
            return _while_any_button(buttons[0])
        return _when_buttons(CallbackType.WHILE_MOUSE_PRESSED, buttons)

    def distance_to(self, x: int | float, y: int | float):
        """Get the distance from the mouse to a point.
        :param x: The x-coordinate of the point.
        :param y: The y-coordinate of the point.
        :return: The distance from the mouse to the point."""
        assert x is not None and y is not None, "x and y must not be None"

        return _math.dist((self.x, self.y), (x, y))


MOUSE_BUTTONS = {1: "left", 2: "middle", 3: "right", 6: "back", 7: "forward"}


def _is_a_single_function(buttons):
    """Whether a mouse decorator was used bare, on a function."""
    return len(buttons) == 1 and callable(buttons[0])


def _check_buttons(buttons):
    """Raise a ValueError unless every entry names a known mouse button."""
    names = ", ".join(repr(name) for name in MOUSE_BUTTONS.values())
    if not buttons:
        raise ValueError(f"Name at least one mouse button: {names}.")
    for button in buttons:
        combination = button if isinstance(button, list) else [button]
        if not combination or any(
            name not in MOUSE_BUTTONS.values() for name in combination
        ):
            raise ValueError(
                f"Mouse button must be one of {names}, or a list of them; "
                f"got {button!r}."
            )


def _when_any_button(callback_type, func):
    """Register *func* to run, without arguments, for any mouse button."""
    async_callback = make_async(func)

    async def wrapper():
        await run_async_callback(
            async_callback,
            [],
            [],
        )

    callback_manager.add_callback(
        callback_type,
        wrapper,
    )
    return wrapper


def _while_any_button(func):
    """Register *func* to run every frame while any mouse button is held."""
    async_callback = make_async(func)

    async def wrapper():
        wrapper.is_running = True
        await run_async_callback(
            async_callback,
            [],
            [],
        )
        wrapper.is_running = False

    wrapper.is_running = False
    callback_manager.add_callback(
        CallbackType.WHILE_MOUSE_PRESSED,
        wrapper,
    )
    return wrapper


def _when_buttons(callback_type, buttons):
    """Return a decorator that registers a function for the named mouse buttons."""
    _check_buttons(buttons)

    def decorator(func):
        async_callback = make_async(func)

        async def wrapper(active_button):
            wrapper.is_running = True
            await run_async_callback(async_callback, [], ["button"], active_button)
            wrapper.is_running = False

        wrapper.is_running = False

        for button in buttons:
            if isinstance(button, list):
                button = frozenset(button)
            callback_manager.add_callback(callback_type, wrapper, button)
        return wrapper

    return decorator


mouse = Mouse()
