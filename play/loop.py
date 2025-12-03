"""This module is used to create a global event loop for the application."""

import asyncio
import sys

# Python 3.14+ changed asyncio.get_event_loop() behavior
# It no longer automatically creates a new event loop if one doesn't exist
if sys.version_info >= (3, 14):
    asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
else:
    loop = asyncio.get_event_loop()

loop.set_debug(False)
