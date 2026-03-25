"""A bunch of random math functions."""

import warnings
from functools import wraps
import inspect
from typing import Sequence

import pygame


def run_once(f):
    """Decorator that ensures a function runs at most once.

    After the first call, subsequent calls are silently ignored.
    Reset by setting ``f.has_run = False``.
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not wrapper.has_run:
            wrapper.has_run = True
            return f(*args, **kwargs)
        return None

    wrapper.has_run = False
    return wrapper


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


def clamp(num, min_, max_):
    """Clamp a number between a minimum and maximum value."""
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
    Turn an English color name or hex code into an RGB value.

    lightBlue
    light-blue
    light blue
    #FF0000
    #f00

    are all valid and will produce an RGB value.
    """
    if isinstance(name, tuple):
        return name

    # Handle hex color codes (#RGB or #RRGGBB)
    stripped = name.strip()
    if stripped.startswith("#"):
        hex_val = stripped[1:]
        if len(hex_val) == 3:
            # Expand shorthand: #F00 -> FF0000
            hex_val = hex_val[0] * 2 + hex_val[1] * 2 + hex_val[2] * 2
        if len(hex_val) == 6:
            try:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
                return (r, g, b, transparency)
            except ValueError:
                pass
        raise ValueError(
            f"You gave an invalid hex color code: '{name}'\n"
            "Hex codes should be 3 or 6 hex digits after '#', like '#FF0000' or '#F00'.\n"
        )

    try:
        color = pygame.color.THECOLORS[
            stripped.lower().replace("-", "").replace(" ", "")
        ]
        # Make the last item of the tuple the transparency value
        color = (color[0], color[1], color[2], transparency)
        return color
    except KeyError as exception:
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
