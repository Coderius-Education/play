"""This module contains the Text class, which is a text string in the game."""

import math as _math
import os
import pygame
from .sprite import Sprite
from ..io.screen import convert_pos
from ..utils import color_name_to_rgb as _color_name_to_rgb
from ..io.logging import play_logger


class Text(Sprite):
    def __init__(
        self,
        words="",
        x=0,
        y=0,
        font="default",
        font_size=50,
        color="black",
        angle=0,
        transparency=100,
        size=100,
    ):
        self._font = font
        self._font_size = font_size

        self._load_font(font, font_size)
        self._words = words
        self._color = color

        self._x = x
        self._y = y

        self._size = size
        self._angle = angle
        self._transparency = transparency

        self._is_clicked = False
        self._is_hidden = False

        self.rect = pygame.Rect(0, 0, 0, 0)
        self._should_recompute = True
        self.update()  # Must compute rect size before start_physics
        super().__init__()

    def update(self):
        """Update the text object."""
        if self._should_recompute:
            pos = convert_pos(self.x, self.y)
            draw_image = self._pygame_font.render(
                self._words, True, _color_name_to_rgb(self._color)
            )
            if self._size != 100:
                new_w = max(round(draw_image.get_width() * self._size / 100), 1)
                new_h = max(round(draw_image.get_height() * self._size / 100), 1)
                draw_image = pygame.transform.scale(draw_image, (new_w, new_h))
            if hasattr(self, "physics") and self.physics is not None:
                angle_deg = _math.degrees(self.physics._pymunk_body.angle)
            else:
                angle_deg = self._angle
            if angle_deg:
                draw_image = pygame.transform.rotate(draw_image, angle_deg)
            draw_image.set_alpha(round(self._transparency * 255 / 100))
            self._image = draw_image
            self.rect = draw_image.get_rect()
            self.rect.center = pos
        super().update()

    def clone(self):
        return self.__class__(
            words=self.words,
            font=self.font,
            font_size=self.font_size,
            color=self.color,
            **self._common_properties(),
        )

    @property
    def words(self):
        """Get the words of the text object."""
        return self._words

    @words.setter
    def words(self, string):
        """Set the words of the text object."""
        self._words = str(string)

    @property
    def font(self):
        """Get the font of the text object."""
        return self._font

    @font.setter
    def font(self, font_name):
        """Set the font of the text object. This will load the font dynamically."""
        self._font = font_name
        self._load_font(font_name, self._font_size)

    @property
    def font_size(self):
        """Get the font size of the text object."""
        return self._font_size

    @font_size.setter
    def font_size(self, size):
        """Set the font size of the text object."""
        self._font_size = size
        self._load_font(self._font, size)

    @property
    def color(self):
        """Get the color of the text object."""
        return self._color

    @color.setter
    def color(self, color_):
        """Set the color of the text object."""
        self._color = color_

    def _load_font(self, font_name, font_size):
        """Helper method to load a font, either from a file or system."""
        if font_name == "default":
            self._pygame_font = pygame.font.Font(
                pygame.font.get_default_font(), font_size
            )
        elif os.path.isfile(font_name):
            self._pygame_font = pygame.font.Font(font_name, font_size)
        else:
            matched = pygame.font.match_font(font_name)
            if matched:
                self._pygame_font = pygame.font.Font(matched, font_size)
            else:
                play_logger.warning(f"Font '{font_name}' not found, using default font")
                self._pygame_font = pygame.font.Font(
                    pygame.font.get_default_font(), font_size
                )
