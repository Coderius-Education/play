"""A bunch of random math functions."""

import os
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
        # iscoroutinefunction unwraps functools.partial, which has no __name__.
        name = getattr(func, "__name__", repr(func))
        raise TypeError(f"{name} is async. {kind} callbacks must be regular functions.")


def load_font(font_path_or_none, size):
    """Load a pygame font from a .ttf path, or fall back to the system default."""
    if font_path_or_none and font_path_or_none != "default":
        try:
            return pygame.font.Font(font_path_or_none, size)
        except (OSError, ValueError, pygame.error):
            # A zero-byte or corrupt font file raises ValueError, and
            # pygame.error derives from RuntimeError, not OSError — neither
            # was caught before, so the fallback never ran for those.
            pass
    return pygame.font.SysFont(None, size)


def render_text(font, text, antialias, color):
    """Render *text*, tolerating strings that come out with no width.

    pygame raises ``error: Text has zero width`` for text that renders to
    nothing (a soft hyphen, a zero-width space), which would end the program
    over an invisible character in a label.
    """
    try:
        return font.render(text, antialias, color)
    except pygame.error:
        return pygame.Surface((0, font.get_height()), pygame.SRCALPHA)


_PYGAME_PREFIX = (
    os.path.normcase(os.path.dirname(os.path.abspath(pygame.__file__))) + os.sep
)


def is_called_from_pygame():
    """Check if the current method is being called from pygame's internal code.

    Matched against pygame's real package directory rather than by looking for
    substrings in the path. The old check also required "site-packages", which
    Debian and Ubuntu do not use — they install to dist-packages — so it could
    never match there and every internal call from pygame.sprite warned the
    user about their own library's normal behaviour. Testing for a bare
    "pygame" substring fails the other way: it would silence a genuine warning
    for anyone whose project happens to live under a path containing "pygame".

    Walks the frames directly instead of using inspect.stack(), which builds a
    full FrameInfo list and reads source context for every frame; this runs on
    every sprite add and remove.
    """
    frame = inspect.currentframe()
    while frame is not None:
        if os.path.normcase(frame.f_code.co_filename).startswith(_PYGAME_PREFIX):
            return True
        frame = frame.f_back
    return False


def check_value_range(min_value, max_value, widget_name):
    """Reject a back-to-front value range with an explanation.

    A swapped range is silently useless rather than loud: the widget clamps
    every value to min_value and its span is negative, so a slider freezes and
    a progress bar reads empty while ``value`` says otherwise. Saying so at the
    line that made the widget is far kinder than leaving a beginner to wonder
    why nothing moves.

    An *equal* range is left alone: ``percentage`` returning 0.0 for a zero
    span is existing, deliberately tested behaviour (see
    test_progress_bar_percentage_zero_span), so only a genuine swap is an
    error here.
    """
    if min_value > max_value:
        raise ValueError(
            f"""The {widget_name} you made has min_value={min_value} and max_value={max_value}.
min_value has to be smaller than max_value, otherwise the {widget_name} can never move.
Try swapping them around: min_value={max_value}, max_value={min_value}\n"""
        )
