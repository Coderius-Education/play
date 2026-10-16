"""
This module contains a decorator that listens to exceptions in the game loop.
"""

import functools
import inspect
import traceback

from play.io.logging import play_logger
from play.loop import (
    first_error_to_show as _first_error_to_show,
    stop_loop as _stop_loop,
)


# @decorator
def listen_to_failure():
    """A decorator that listens to exceptions in the game loop."""

    def decorate(f):
        _is_async = inspect.iscoroutinefunction(f)

        @functools.wraps(f)
        async def applicator(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                if _is_async:
                    return await result
                return result
            except Exception as e:
                _stop_loop()
                if _first_error_to_show():
                    play_logger.critical(
                        "Error in %s:\n%s",
                        f.__name__,
                        "".join(traceback.format_exception(e)),
                    )
                raise

        return applicator

    return decorate
