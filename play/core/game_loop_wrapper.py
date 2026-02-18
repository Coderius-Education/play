"""
This module contains a decorator that listens to exceptions in the game loop.
"""

import asyncio

from ..io.logging import play_logger
from ..loop import loop as _loop


# @decorator
def listen_to_failure():
    """A decorator that listens to exceptions in the game loop."""

    def decorate(f):
        async def applicator(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except Exception as e:
                _loop.stop()
                play_logger.critical("Error in %s: %s", f.__name__, e)
                raise e

        return applicator

    return decorate
