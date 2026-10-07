"""This module defines the Circle class, which represents a circle in the game."""

import pygame
from .sprite import Sprite
from ..utils import color_name_to_rgb as _color_name_to_rgb


class Circle(Sprite):
    _circular_hit_shape = True

    def __init__(
        self,
        color="black",
        x=0,
        y=0,
        radius=100,
        border_color="light blue",
        border_width=0,
        transparency=100,
        size=100,
        angle=0,
        anchor=None,
        layer=0,
    ):
        self._color = color
        self._radius = radius
        self._border_color = border_color
        self._border_width = border_width
        self._transparency = transparency
        self._size = size
        self._angle = angle
        self.rect = pygame.Rect(0, 0, 0, 0)

        super().__init__(x=x, y=y, anchor=anchor, layer=layer)
        self.update()

    def _hit_dims(self, size_factor):
        """Circle hit-shape uses its radius, scaled by size."""
        return self._radius * size_factor, 0.0, 0.0

    def clone(self):
        """Create a copy of the circle.
        :return: A copy of the circle."""
        return self.__class__(
            color=self.color,
            radius=self.radius,
            border_color=self.border_color,
            border_width=self.border_width,
            **self._common_properties(),
        )

    def _render(self):
        """Draw the circle surface with border, scale, alpha, and rotation."""
        draw_image = pygame.Surface(
            (self._radius * 2, self._radius * 2), pygame.SRCALPHA
        )

        if self._border_width > 0:
            pygame.draw.circle(
                draw_image,
                _color_name_to_rgb(self._border_color),
                (self._radius, self._radius),
                self._radius,
            )

        pygame.draw.circle(
            draw_image,
            _color_name_to_rgb(self._color),
            (self._radius, self._radius),
            max(self._radius - self._border_width, 0),
        )

        if self._size <= 0:
            draw_image = pygame.Surface((0, 0), pygame.SRCALPHA)
        elif self._size != 100:
            # Round the radius, not the diameter, so the picture stays even-sized
            # and its centre on a whole pixel. Never below a radius of one.
            scaled_r = max(round(self._radius * self._size / 100), 1)
            draw_image = pygame.transform.scale(
                draw_image, (scaled_r * 2, scaled_r * 2)
            )

        self._place_image(draw_image)

    ##### color #####
    @property
    def color(self):
        """The color of the circle.
        :return: The color of the circle."""
        return self._color

    @color.setter
    def color(self, _color):
        """Set the color of the circle.
        :param _color: The color of the circle."""
        _color_name_to_rgb(_color)
        self._color = _color

    def _info_size(self):
        return f"radius={self.radius}"

    ##### radius #####
    @property
    def radius(self):
        """The radius of the circle.
        :return: The radius of the circle."""
        return self._radius

    @radius.setter
    def radius(self, _radius):
        """Set the radius of the circle.
        :param _radius: The radius of the circle."""
        self._radius = _radius
        # Account for size scaling when updating physics shape
        size_factor = (self._size or 100) / 100
        self.physics._pymunk_shape.unsafe_set_radius(self._radius * size_factor)

    ##### border_color #####
    @property
    def border_color(self):
        """The color of the circle's border.
        :return: The color of the circle's border."""
        return self._border_color

    @border_color.setter
    def border_color(self, _border_color):
        """Set the color of the circle's border.
        :param _border_color: The color of the circle's border."""
        _color_name_to_rgb(_border_color)
        self._border_color = _border_color

    ##### border_width #####
    @property
    def border_width(self):
        """The width of the circle's border.
        :return: The width of the circle's border."""
        return self._border_width

    @border_width.setter
    def border_width(self, _border_width):
        """Set the width of the circle's border.
        :param _border_width: The width of the circle's border."""
        self._border_width = _border_width
