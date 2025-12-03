"""This module is used to create a global event loop for the application."""

import sys
import asyncio
import traceback
from .io.logging import play_logger


def _handle_exception(the_loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"

    if exception:
        tb_lines = traceback.format_exception(
            type(exception), exception, exception.__traceback__
        )
        tb_str = "".join(tb_lines)
        play_logger.critical("Unhandled exception in task '%s':\n%s", task_name, tb_str)
    else:
        play_logger.critical(
            context.get("message", "Unhandled exception in async task")
        )

    the_loop.stop()


# Python 3.14+ changed asyncio.get_event_loop() behavior
# It no longer automatically creates a new event loop if one doesn't exist
if sys.version_info >= (3, 14):
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

loop.set_debug(False)
loop.set_exception_handler(_handle_exception)
