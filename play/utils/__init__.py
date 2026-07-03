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

    stripped = name.strip()
    # Expand shorthand hex: #F00 -> #FF0000
    if stripped.startswith("#") and len(stripped) == 4:
        stripped = "#" + stripped[1] * 2 + stripped[2] * 2 + stripped[3] * 2

    # Normalize color names: "light blue", "light-blue", "lightBlue" -> "lightblue"
    color_str = (
        stripped
        if stripped.startswith("#")
        else stripped.lower().replace("-", "").replace(" ", "")
    )

    try:
        c = pygame.Color(color_str)
        return (c.r, c.g, c.b, transparency)
    except ValueError as exc:
        raise ValueError(
            f"""You gave a color name we didn't understand: '{name}'
Try using a hex code like '#FF0000' or '#F00',
or the RGB number form e.g. '(0, 255, 255)'.
You can find the RGB form of a color on websites like this: https://www.rapidtables.com/web/color/RGB_Color.html\n"""
        ) from exc


def reject_async_callback(func, kind):
    """Raise TypeError if *func* is a coroutine function.

    Widget callback registrars (when_changed/when_submit/when_hover/...) run
    synchronously, so an ``async def`` handler would never be awaited. *kind* is
    the registrar name used in the error message."""
    if inspect.iscoroutinefunction(func):
        raise TypeError(
            f"{func.__name__} is async. {kind} callbacks must be regular functions."
        )


def load_font(font_path_or_none, size):
    """Load a pygame font from a .ttf path, or fall back to the system default."""
    if font_path_or_none and font_path_or_none != "default":
        try:
            return pygame.font.Font(font_path_or_none, size)
        except (FileNotFoundError, OSError):
            pass
    return pygame.font.SysFont(None, size)


def is_called_from_pygame():
    """Check if the current method is being called from pygame's internal code."""
    stack = inspect.stack()

    for frame_info in stack:
        filename = frame_info.filename
        if "pygame" in filename and "site-packages" in filename:
            return True
    return False
