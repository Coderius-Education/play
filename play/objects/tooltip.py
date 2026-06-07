"""Tooltip — a text overlay that appears when hovering over a target sprite."""

import math as _math
import pygame

from .sprite import Sprite
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb
from ..io.screen import convert_pos


def _load_font(font_path_or_none, size):
    if font_path_or_none and font_path_or_none != "default":
        try:
            return pygame.font.Font(font_path_or_none, size)
        except (FileNotFoundError, OSError):
            pass
    return pygame.font.SysFont(None, size)


class Tooltip(Sprite):
    """A floating text label that follows the mouse and is only visible while
    the mouse hovers over *target*.

    Usage::

        btn = play.new_button("Hover me")
        tip = play.new_tooltip("Click to continue", target=btn)
    """

    def __init__(
        self,
        text="",
        target=None,
        offset_x=12,
        offset_y=-12,
        color="lightyellow",
        text_color="black",
        border_color="gray",
        font_size=15,
        font=None,
        padding=6,
        border_radius=4,
        transparency=100,
        layer=100,
    ):
        self._tooltip_text = text
        self._target = target
        self._offset_x = offset_x
        self._offset_y = offset_y
        self._tooltip_color = color
        self._text_color = text_color
        self._border_color = border_color
        self._tooltip_font = _load_font(font, font_size)
        self._font_size = font_size
        self._font_path = font
        self._padding = padding
        self._border_radius = border_radius
        self._transparency = transparency
        self._size = 100
        self._angle = 0
        self._image = None
        self.rect = pygame.Rect(0, 0, 0, 0)
        super().__init__(x=0, y=0, layer=layer)
        self._is_hidden = True
        self.update()

    def update(self):
        """Show/hide based on whether the mouse is over the target."""
        if self._target is not None:
            hovered = mouse.is_touching(self._target)
            if hovered and self._is_hidden:
                self._is_hidden = False
                self._should_recompute = True
            elif not hovered and not self._is_hidden:
                self._is_hidden = True
                self._should_recompute = True

        if not self._is_hidden:
            # Follow the mouse position
            from ..io.screen import screen
            self._x = mouse.x + self._offset_x
            self._y = mouse.y + self._offset_y
            self._should_recompute = True

        super().update()

    def _render(self):
        """Render the tooltip bubble."""
        font = self._tooltip_font
        lines = self._tooltip_text.split("\n")
        rendered = [font.render(ln, True, _color_name_to_rgb(self._text_color)) for ln in lines]

        text_w = max(s.get_width() for s in rendered) if rendered else 0
        text_h = sum(s.get_height() for s in rendered) + max(0, len(rendered) - 1) * 2
        p = self._padding
        w = text_w + 2 * p
        h = text_h + 2 * p

        draw_image = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(
            draw_image, _color_name_to_rgb(self._tooltip_color), (0, 0, w, h),
            border_radius=self._border_radius,
        )
        pygame.draw.rect(
            draw_image, _color_name_to_rgb(self._border_color), (0, 0, w, h),
            1, border_radius=self._border_radius,
        )

        y = p
        for surf in rendered:
            draw_image.blit(surf, (p, y))
            y += surf.get_height() + 2

        draw_image.set_alpha(round(self._transparency * 255 / 100))

        self.rect = draw_image.get_rect()
        pos = convert_pos(self._x, self._y)
        self.rect.x = pos[0]
        self.rect.y = pos[1] - h
        angle_deg = _math.degrees(self.physics._pymunk_body.angle)
        self.image = pygame.transform.rotate(draw_image, angle_deg)
        self.rect = self.image.get_rect(topleft=self.rect.topleft)

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def text(self):
        """The tooltip text (may include newlines)."""
        return self._tooltip_text

    @text.setter
    def text(self, v):
        self._tooltip_text = v
        self._should_recompute = True

    @property
    def target(self):
        """The sprite this tooltip is attached to."""
        return self._target

    @target.setter
    def target(self, v):
        self._target = v
