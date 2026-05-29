"""This module contains the Button class, a Box with a text label and hover state."""

import pygame

from .box import Box
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb


class Button(Box):
    def __init__(
        self,
        text="Button",
        x=0,
        y=0,
        width=160,
        height=50,
        color="royalblue",
        hover_color="steelblue",
        text_color="white",
        font_size=20,
        border_radius=6,
        transparency=100,
        size=100,
        anchor=None,
        layer=10,
    ):
        self._button_text = text
        self._hover_color = hover_color
        self._base_color = color
        self._text_color = text_color
        self._button_font_size = font_size
        super().__init__(
            color=color,
            x=x,
            y=y,
            width=width,
            height=height,
            border_radius=border_radius,
            transparency=transparency,
            size=size,
            anchor=anchor,
            layer=layer,
        )

    def update(self):
        """Draw box with hover colour, then blit text on top."""
        if self._anchor:
            self._apply_anchor()
        hovered = (
            self.x - self._width / 2 <= mouse.x <= self.x + self._width / 2
            and self.y - self._height / 2 <= mouse.y <= self.y + self._height / 2
        )
        self._color = self._hover_color if hovered else self._base_color
        needs_text = self._should_recompute
        super().update()
        if needs_text and self.image is not None:
            self._blit_text()

    def _blit_text(self):
        font = pygame.font.SysFont(None, self._button_font_size)
        text_surf = font.render(
            self._button_text, True, _color_name_to_rgb(self._text_color)
        )
        text_rect = text_surf.get_rect(
            center=(self.image.get_width() // 2, self.image.get_height() // 2)
        )
        self.image.blit(text_surf, text_rect)

    @property
    def text(self):
        """The button label."""
        return self._button_text

    @text.setter
    def text(self, value):
        """Set the button label and trigger a redraw."""
        self._button_text = value
        self._should_recompute = True
