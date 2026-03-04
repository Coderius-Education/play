"""
This module contains a decorator that listens to exceptions in the game loop.
"""

import asyncio
import functools

from ..io.logging import play_logger
from ..loop import get_loop as _get_loop


# @decorator
def listen_to_failure():
    """A decorator that listens to exceptions in the game loop."""

    def decorate(f):
        if asyncio.iscoroutinefunction(f):

            @functools.wraps(f)
            async def applicator(*args, **kwargs):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    _get_loop().stop()
                    play_logger.critical("Error in %s: %s", f.__name__, e)
                    raise e

        else:

            @functools.wraps(f)
            async def applicator(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    _get_loop().stop()
                    play_logger.critical("Error in %s: %s", f.__name__, e)
                    raise e

        return applicator

    return decorate
