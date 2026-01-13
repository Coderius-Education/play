"""This module contains the Text class, which is a text string in the game."""

import pygame
import pygame_gui
from ..globals import globals_list

from ..io.screen import convert_pos


class Text:
    def __init__(
        self,
        words="",
        x=0,
        y=0,
        font_size=50,
        color="black",
    ):
        self._font_size = font_size

        self._words = words
        self._color = color

        self._x = x
        self._y = y

        self.text = None  # Will be created after update()

        # Create pygame_gui label
        self._create_gui_label()

    def _create_gui_label(self):
        """Create or update the pygame_gui label based on current position and text."""
        if not globals_list.ui_manager:
            return

        # Convert play coordinates to pygame coordinates
        pygame_x, pygame_y = convert_pos(self._x, self._y)

        # Estimate size based on text length and font size
        estimated_width = max(len(self._words) * self._font_size * 0.6, 50)
        estimated_height = self._font_size * 1.5

        # Calculate top-left position to center the label
        left = int(pygame_x - estimated_width / 2)
        top = int(pygame_y - estimated_height / 2)

        # Create or update the label
        if self.text is None:
            self.text = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    left, top, int(estimated_width), int(estimated_height)
                ),
                text=self._words,
                manager=globals_list.ui_manager,
            )
        else:
            # Update existing label position and text
            self.text.set_relative_position((left, top))
            self.text.set_dimensions((int(estimated_width), int(estimated_height)))
            self.text.set_text(self._words)

    @property
    def words(self):
        """Get the words of the text object."""
        return self._words

    @words.setter
    def words(self, string):
        """Set the words of the text object."""
        self._words = str(string)
        self._create_gui_label()  # Update pygame_gui label

    @property
    def color(self):
        """Get the color of the text object."""
        return self._color

    @color.setter
    def color(self, color_):
        """Set the color of the text object."""
        self._color = color_

    @property
    def x(self):
        """Get the x-coordinate of the text object."""
        return self._x

    @x.setter
    def x(self, value):
        """Set the x-coordinate of the text object."""
        self._x = value
        self._create_gui_label()  # Update pygame_gui label position

    @property
    def y(self):
        """Get the y-coordinate of the text object."""
        return self._y

    @y.setter
    def y(self, value):
        """Set the y-coordinate of the text object."""
        self._y = value
        self._create_gui_label()  # Update pygame_gui label position
