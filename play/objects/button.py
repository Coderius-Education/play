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
        self._button_font = pygame.font.SysFont(None, font_size)
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
        """Set hover colour, delegate rendering to Sprite, then blit text label."""
        self._color = self._hover_color if mouse.is_touching(self) else self._base_color
        needs_text = self._should_recompute
        super().update()  # → Sprite.update() → anchor + Box._render()
        if needs_text and self.image is not None:
            self._blit_text()

    def _blit_text(self):
        text_surf = self._button_font.render(
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

    @property
    def text_color(self):
        """The colour of the button label."""
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value
        self._should_recompute = True

    @property
    def hover_color(self):
        """The background colour when the mouse is over the button."""
        return self._hover_color

    @hover_color.setter
    def hover_color(self, value):
        self._hover_color = value
        self._should_recompute = True

    @property
    def font_size(self):
        """The font size of the button label."""
        return self._button_font_size

    @font_size.setter
    def font_size(self, value):
        self._button_font_size = value
        self._button_font = pygame.font.SysFont(None, value)
        self._should_recompute = True

    def clone(self):
        """Create a copy of this button."""
        return Button(
            text=self._button_text,
            x=self.x,
            y=self.y,
            width=self._width,
            height=self._height,
            color=self._base_color,
            hover_color=self._hover_color,
            text_color=self._text_color,
            font_size=self._button_font_size,
            border_radius=self._border_radius,
            transparency=self._transparency,
            size=self._size,
        )
