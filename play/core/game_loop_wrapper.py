"""
This module contains a decorator that listens to exceptions in the game loop.
"""

import functools
import inspect

from play.globals import globals_list
from play.io.logging import play_logger
from play.loop import stop_loop as _stop_loop


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
                if not globals_list.error_shown:
                    play_logger.critical("Error in %s: %s", f.__name__, e)
                raise

        return applicator

    return decorate
