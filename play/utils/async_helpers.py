"""This module contains code to help with async functions."""

import contextlib as _contextlib
import inspect as _inspect
import linecache as _linecache
import re as _re
import sys as _sys
import warnings as _warnings

from play.io.logging import play_logger

_CREATED_AT = _re.compile(
    r'File "(?P<filename>[^"]+)", line (?P<lineno>\d+), in (?P<function>\S+)'
)


def _is_plain_def(filename, lineno, function):
    """Whether the nearest ``def function`` above *lineno* is a plain, not async, def."""
    for number in range(lineno, 0, -1):
        found = _re.match(
            rf"\s*(async\s+)?def\s+{_re.escape(function)}\b",
            _linecache.getline(filename, number),
        )
        if found:
            return found.group(1) is None
    return False


def _call_as_written(name, filename, lineno):
    """Return *name* as the source line calls it, e.g. ``play.timer``."""
    short_name = name.rsplit(".", 1)[-1]
    source = _linecache.getline(filename, lineno)
    found = _re.search(rf"[\w.]*\b{_re.escape(short_name)}(?=\s*\()", source)
    return found.group(0) if found else name


def _forgot_await_hint(name, filename, lineno, function):
    """Explain how to fix a call to the coroutine *name* that was never awaited."""
    name = _call_as_written(name, filename, lineno)
    hint = (
        f'Looks like you forgot "await" before {name}() '
        f"on line {lineno} of file {filename}.\n"
        f"To fix this, write: await {name}(...)"
    )
    if _is_plain_def(filename, lineno, function):
        hint += (
            f'\nand change "def {function}" into "async def {function}", '
            "because await only works inside an async def."
        )
    return hint


@_contextlib.contextmanager
def hint_forgotten_awaits():
    """Replace "coroutine was never awaited" warnings by a hint, once per line."""
    show_warning = _warnings.showwarning
    tracking_depth = _sys.get_coroutine_origin_tracking_depth()
    hinted = set()

    def show(message, category, filename, lineno, file=None, line=None):
        text = str(message)
        created_at = _CREATED_AT.search(text)
        if not (
            issubclass(category, RuntimeWarning)
            and "was never awaited" in text
            and created_at
        ):
            show_warning(message, category, filename, lineno, file, line)
            return
        where = created_at["filename"], int(created_at["lineno"])
        if where not in hinted:
            hinted.add(where)
            name = text.split("'")[1]
            play_logger.warning(
                _forgot_await_hint(name, *where, created_at["function"])
            )

    _warnings.showwarning = show
    _sys.set_coroutine_origin_tracking_depth(1)
    try:
        yield
    finally:
        _sys.set_coroutine_origin_tracking_depth(tracking_depth)
        _warnings.showwarning = show_warning


def make_async(func):
    """
    Turn a non-async function into an async function.
    Used mainly in decorators like @repeat_forever.
    :param func: A function that may or may not be async.
    """
    if _inspect.iscoroutinefunction(func):
        return func

    async def async_func(*args, **kwargs):
        return func(*args, **kwargs)

    async_func.original_function = func
    return async_func
