"""A bunch of random math functions."""

import warnings
from functools import wraps
import inspect
from typing import Sequence

import pygame


def experimental(cls):
    """
    Decorator to mark a class as experimental.

    When the class is instantiated, a FutureWarning will be issued to inform
    users that the class is experimental and may change in future versions.
    """
    original_init = cls.__init__

    @wraps(original_init)
    def new_init(self, *args, **kwargs):
        warnings.warn(
            f"{cls.__name__} is experimental and may change in future versions. "
            f"Use at your own risk.",
            FutureWarning,
            stacklevel=2,
        )
        original_init(self, *args, **kwargs)

    cls.__init__ = new_init

    # Add experimental marker to docstring
    if cls.__doc__:
        cls.__doc__ = f"**EXPERIMENTAL**: {cls.__doc__}"
    else:
        cls.__doc__ = "**EXPERIMENTAL**: This class is experimental and may change in future versions."

    return cls


def cast_to_number(value, name="value"):
    """Cast a value to a float, raising a friendly error if it fails."""
    try:
        return float(value)
    except (ValueError, TypeError) as exception:
        raise ValueError(
            f"You provided an invalid {name}: '{value}'. {name.capitalize()} must be a number (like 50 or 10.5)."
        ) from exception


def clamp(num, min_, max_, name="value"):
    """Clamp a number between a minimum and maximum value."""
    try:
        num = float(num)
    except (ValueError, TypeError):
        # Fallback to the heavy error generator if it actually fails
        num = cast_to_number(num, name)

    if num < min_:
        return min_
    if num > max_:
        return max_
    return num


class _Position:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, indices):
        if indices == 0:
            return self.x
        if indices == 1:
            return self.y
        raise IndexError()

    def __iter__(self):
        yield self.x
        yield self.y

    def __len__(self):
        return 2

    def __setitem__(self, i, value):
        if i == 0:
            self.x = value
        elif i == 1:
            self.y = value
        else:
            raise IndexError()


def color_name_to_rgb(
    name: str, transparency: int = 255
) -> tuple[int, int, int, int] | tuple | str:
    """
    Turn an English color name into an RGB value.

    lightBlue
    light-blue
    light blue

    are all valid and will produce the rgb value for lightblue.
    """
    if isinstance(name, tuple):
        return name
    try:
        color = pygame.color.THECOLORS[
            name.lower().strip().replace("-", "").replace(" ", "")
        ]
        # Make the last item of the tuple the transparency value
        color = (color[0], color[1], color[2], transparency)
        return color
    except (KeyError, AttributeError) as exception:
        raise ValueError(
            f"""You gave a color name we didn't understand: '{name}'
Try using the RGB number form of the color e.g. '(0, 255, 255)'.
You can find the RGB form of a color on websites like this: https://www.rapidtables.com/web/color/RGB_Color.html\n"""
        ) from exception


def is_called_from_pygame():
    """Check if the current method is being called from pygame's internal code."""
    stack = inspect.stack()

    for frame_info in stack:
        filename = frame_info.filename
        if "pygame" in filename and "site-packages" in filename:
            return True
    return False
