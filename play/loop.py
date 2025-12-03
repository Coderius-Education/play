"""This module is used to create a global event loop for the application."""

import asyncio
import traceback
import pygame
from .io.logging import play_logger


def _handle_exception(loop, context):
    exception = context.get("exception")
    task = context.get("future")
    task_name = task.get_name() if task else "unknown"

    if exception:
        tb_lines = traceback.format_exception(type(exception), exception, exception.__traceback__)
        tb_str = ''.join(tb_lines)
        play_logger.critical(f"Unhandled exception in task '{task_name}':\n{tb_str}")
    else:
        play_logger.critical(context.get("message", "Unhandled exception in async task"))

    loop.stop()


loop = asyncio.get_event_loop()
loop.set_debug(False)
loop.set_exception_handler(_handle_exception)
