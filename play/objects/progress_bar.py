"""ProgressBar — a read-only range display widget (health bar, loading bar, etc.)."""

import math as _math
import pygame

from .box import Box
from ..utils import color_name_to_rgb as _color_name_to_rgb
from ..io.screen import convert_pos


class ProgressBar(Box):
    def __init__(
        self,
        min_value=0,
        max_value=100,
        value=50,
        x=0,
        y=0,
        width=200,
        height=24,
        bar_color="royalblue",
        background_color="lightgray",
        border_color="gray",
        border_width=1,
        border_radius=4,
        transparency=100,
        anchor=None,
        layer=0,
        show_label=False,
        label_color="white",
        font_size=14,
        font=None,
    ):
        self._min_value = min_value
        self._max_value = max_value
        self._bar_value = max(min_value, min(max_value, value))
        self._bar_color = bar_color
        self._background_color = background_color
        self._show_label = show_label
        self._label_color = label_color
        self._font_size = font_size
        self._font_path = font
        if font and font != "default":
            try:
                self._font = pygame.font.Font(font, font_size)
            except (FileNotFoundError, OSError):
                self._font = pygame.font.SysFont(None, font_size)
        else:
            self._font = pygame.font.SysFont(None, font_size)

        super().__init__(
            color=background_color,
            x=x,
            y=y,
            width=width,
            height=height,
            border_color=border_color,
            border_width=border_width,
            border_radius=border_radius,
            transparency=transparency,
            anchor=anchor,
            layer=layer,
        )

    def _render(self):
        """Draw the background bar then the filled portion."""
        w, h = self._width, self._height
        bw = self._border_width
        draw_image = pygame.Surface((w, h), pygame.SRCALPHA)

        # Background
        if bw > 0:
            pygame.draw.rect(
                draw_image,
                _color_name_to_rgb(self._border_color),
                (0, 0, w, h),
                bw,
                border_radius=self._border_radius,
            )
        pygame.draw.rect(
            draw_image,
            _color_name_to_rgb(self._background_color),
            (bw, bw, w - 2 * bw, h - 2 * bw),
            border_radius=max(0, self._border_radius - bw),
        )

        # Filled portion
        span = max(1, self._max_value - self._min_value)
        t = max(0.0, min(1.0, (self._bar_value - self._min_value) / span))
        inner_w = w - 2 * bw
        fill_w = int(t * inner_w)
        if fill_w > 0:
            pygame.draw.rect(
                draw_image,
                _color_name_to_rgb(self._bar_color),
                (bw, bw, fill_w, h - 2 * bw),
                border_radius=max(0, self._border_radius - bw),
            )

        # Optional percentage label
        if self._show_label:
            pct = int(t * 100)
            label_surf = self._font.render(
                f"{pct}%", True, _color_name_to_rgb(self._label_color)
            )
            lx = (w - label_surf.get_width()) // 2
            ly = (h - label_surf.get_height()) // 2
            draw_image.blit(label_surf, (lx, ly))

        draw_image.set_alpha(round(self._transparency * 255 / 100))

        self.rect = draw_image.get_rect()
        pos = convert_pos(self.x, self.y)
        self.rect.x = pos[0] - self.rect.width // 2
        self.rect.y = pos[1] - self.rect.height // 2
        angle_deg = _math.degrees(self.physics._pymunk_body.angle)
        self.image = pygame.transform.rotate(draw_image, angle_deg)
        self.rect = self.image.get_rect(center=self.rect.center)

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def value(self):
        """The current progress value."""
        return self._bar_value

    @value.setter
    def value(self, v):
        self._bar_value = max(self._min_value, min(self._max_value, v))
        self._should_recompute = True

    @property
    def min_value(self):
        """The minimum value of the progress bar range."""
        return self._min_value

    @min_value.setter
    def min_value(self, v):
        self._min_value = v
        self._bar_value = max(v, self._bar_value)
        self._should_recompute = True

    @property
    def max_value(self):
        """The maximum value of the progress bar range."""
        return self._max_value

    @max_value.setter
    def max_value(self, v):
        self._max_value = v
        self._bar_value = min(v, self._bar_value)
        self._should_recompute = True

    @property
    def bar_color(self):
        """The colour of the filled portion of the bar."""
        return self._bar_color

    @bar_color.setter
    def bar_color(self, v):
        self._bar_color = v
        self._should_recompute = True

    @property
    def percentage(self):
        """The current value expressed as a fraction between 0.0 and 1.0."""
        span = max(1, self._max_value - self._min_value)
        return max(0.0, min(1.0, (self._bar_value - self._min_value) / span))

    def clone(self):
        return ProgressBar(
            min_value=self._min_value,
            max_value=self._max_value,
            value=self._bar_value,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            width=self._width,
            height=self._height,
            bar_color=self._bar_color,
            background_color=self._background_color,
            border_color=self._border_color,
            border_width=self._border_width,
            border_radius=self._border_radius,
            transparency=self._transparency,
            anchor=self._anchor,
            layer=self._layer,
            show_label=self._show_label,
            label_color=self._label_color,
            font_size=self._font_size,
            font=self._font_path,
        )
