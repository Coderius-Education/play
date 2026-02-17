"""This module provides a wrapper around the Pygame display module to create a screen object"""

import pygame
import pymunk as _pymunk

from ..callback import run_callback, CallbackType, callback_manager
from ..callback.collision_callbacks import WallSide
from ..globals import globals_list
from ..physics import physics_space
from ..utils.async_helpers import make_async

PYGAME_DISPLAY = None


class Screen:
    def update_display(self, extra_flags=0):
        """Update the display with the current width and height."""
        flags = pygame.DOUBLEBUF | extra_flags
        if self._resizable:
            flags |= pygame.RESIZABLE
        globals_list.display = pygame.display.set_mode(
            (self._width, self._height),
            flags,
        )

    def __init__(self, width=globals_list.WIDTH, height=globals_list.HEIGHT):
        self._width = width
        self._height = height

        self._resizable = False
        self._fullscreen = False
        self._caption = "coderius-play"

        self.update_display()
        pygame.display.set_caption(self._caption)

    @property
    def caption(self):
        """Get the caption of the screen.
        :return: The caption of the screen."""
        return self._caption

    @caption.setter
    def caption(self, _caption):
        """Set the caption of the screen.
        :param _caption: The new caption of the screen."""
        self._caption = _caption
        pygame.display.set_caption(self._caption)

    @property
    def resizable(self):
        """Get whether the screen is resizable.
        :return: Whether the screen is resizable."""
        return self._resizable

    @resizable.setter
    def resizable(self, _resizable):
        """Set whether the screen is resizable.
        :param _resizable: Whether the screen is resizable."""
        self._resizable = _resizable

    @property
    def width(self):
        """Get the width of the screen.
        :return: The width of the screen."""
        return self._width

    @width.setter
    def width(self, _width):
        """Set the width of the screen.
        :param _width: The new width of the screen."""
        self._width = _width

    @property
    def height(self):
        """Get the height of the screen.
        :return: The height of the screen."""
        return self._height

    @height.setter
    def height(self, _height):
        """Set the height of the screen.
        :param _height: The new height of the screen."""
        self._height = _height

    @property
    def top(self):
        """Get the top side of the screen.
        :return: The top side of the screen."""
        return self.height / 2

    @property
    def bottom(self):
        """Get the bottom side of the screen.
        :return: The bottom side of the screen."""
        return self.height / -2

    @property
    def left(self):
        """Get the left side of the screen.
        :return: The left side of the screen."""
        return self.width / -2

    @property
    def right(self):
        """Get the right side of the screen.
        :return: The right side of the screen."""
        return self.width / 2

    @property
    def size(self):
        """Get the size of the screen.
        :return: The size of the screen."""
        return self.width, self.height

    def when_resized(self, func):
        """Run a function when the screen is resized.
        :param func: The function to run."""
        async_callback = make_async(func)

        async def wrapper():
            await run_callback(
                async_callback,
                [],
                [],
            )

        callback_manager.add_callback(
            CallbackType.WHEN_RESIZED,
            wrapper,
        )
        return wrapper

    def resize(self, new_width, new_height):
        """Resize the screen to new dimensions.

        :param new_width: The new width of the screen
        :param new_height: The new height of the screen
        :raises RuntimeError: If sprites have already been created
        """
        # Check if any sprites exist
        if len(globals_list.sprites_group) > 0:
            sprite_count = len(globals_list.sprites_group)
            sprite_word = "sprite" if sprite_count == 1 else "sprites"
            raise RuntimeError(
                f"Screen must be resized before creating sprites.\n\n"
                f"Problem: You called play.screen.resize() after creating {sprite_count} {sprite_word}.\n"
                f"Solution: Move play.screen.resize() to the beginning of your script:\n\n"
                f"    import play\n"
                f"    play.screen.resize({new_width}, {new_height})  # ← Move this here\n"
                f"    cirkel = play.new_circle()     # ← Before creating sprites\n"
            )

        self.width = new_width
        self.height = new_height
        self.update_display()


screen = Screen()


def create_wall(a, b, wall_side):
    """Create a wall segment in the physics space.
    :param a: The start point of the wall segment.
    :param b: The end point of the wall segment.
    :param wall_side: The side of the screen this wall represents (WallSide enum)."""
    segment = _pymunk.Segment(physics_space.static_body, a, b, 0.0)
    segment.elasticity = 1.0
    segment.friction = 0.0
    segment.wall_side = wall_side
    physics_space.add(segment)
    return segment


def create_walls():
    """Create walls around the screen."""
    globals_list.walls.append(
        create_wall([screen.left, screen.top], [screen.right, screen.top], WallSide.TOP)
    )
    globals_list.walls.append(
        create_wall(
            [screen.left, screen.bottom], [screen.right, screen.bottom], WallSide.BOTTOM
        )
    )
    globals_list.walls.append(
        create_wall(
            [screen.left, screen.bottom], [screen.left, screen.top], WallSide.LEFT
        )
    )
    globals_list.walls.append(
        create_wall(
            [screen.right, screen.bottom], [screen.right, screen.top], WallSide.RIGHT
        )
    )


def remove_walls():
    """Remove the walls from the physics space."""
    for wall in globals_list.walls:
        physics_space.remove(wall)
    globals_list.walls.clear()


def remove_wall(index):
    """Remove a wall from the physics space.
    :param index: The index of the wall to remove. 0: top, 1: bottom, 2: left, 3: right.
    """
    physics_space.remove(globals_list.walls[index])
    globals_list.walls.pop(index)


create_walls()


def convert_pos(x, y):
    """
    Convert from the Play coordinate system to the Pygame coordinate system.
    :param x: The x-coordinate in the Play coordinate system.
    :param y: The y-coordinate in the Play coordinate system.
    """
    x1 = screen.width / 2 + x
    y1 = screen.height / 2 - y
    return x1, y1


def pos_convert(x, y):
    """
    Convert from the Pygame coordinate system to the Play coordinate system.
    :param x: The x-coordinate in the Pygame coordinate system.
    :param y: The y-coordinate in the Pygame coordinate system.
    """
    x1 = x - screen.width / 2
    y1 = screen.height / 2 - y
    return x1, y1
