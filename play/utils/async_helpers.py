"""This module contains code to help with async functions."""

import contextlib as _contextlib
import inspect as _inspect
import linecache as _linecache
import re as _re
import warnings as _warnings

from play.io.logging import play_logger


def _code_at(filename, lineno):
    """Return the code object running at *filename*:*lineno* on the stack, or None."""
    frame = _inspect.currentframe()
    while frame is not None:
        if frame.f_code.co_filename == filename and frame.f_lineno == lineno:
            return frame.f_code
        frame = frame.f_back
    return None


def _call_as_written(name, filename, lineno):
    """Return *name* as the source line calls it, e.g. ``play.timer``."""
    short_name = name.rsplit(".", 1)[-1]
    source = _linecache.getline(filename, lineno)
    found = _re.search(rf"[\w.]*\b{_re.escape(short_name)}(?=\s*\()", source)
    return found.group(0) if found else name


def _forgot_await_hint(name, filename, lineno):
    """Explain how to fix a call to the coroutine *name* that was never awaited."""
    name = _call_as_written(name, filename, lineno)
    hint = (
        f'Looks like you forgot "await" before {name}() '
        f"on line {lineno} of file {filename}.\n"
        f"To fix this, write: await {name}(...)"
    )
    code = _code_at(filename, lineno)
    if code is not None and not code.co_flags & _inspect.CO_COROUTINE:
        hint += (
            f'\nand change "def {code.co_name}" into "async def {code.co_name}", '
            "because await only works inside an async def."
        )
    return hint


@_contextlib.contextmanager
def hint_forgotten_awaits():
    """Replace "coroutine was never awaited" warnings by a hint, once per line."""
    show_warning = _warnings.showwarning
    hinted = set()

    def show(message, category, filename, lineno, file=None, line=None):
        text = str(message)
        if not (issubclass(category, RuntimeWarning) and "was never awaited" in text):
            show_warning(message, category, filename, lineno, file, line)
            return
        if (filename, lineno) not in hinted:
            hinted.add((filename, lineno))
            name = text.split("'")[1]
            play_logger.warning(_forgot_await_hint(name, filename, lineno))

    _warnings.showwarning = show
    try:
        yield
    finally:
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
