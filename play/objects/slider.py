"""Slider — a draggable range-input widget."""

import inspect as _inspect
import math as _math
import pygame

from .sprite import Sprite
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb, load_font as _load_font
from ..io.screen import convert_pos, screen
from ..core.mouse_loop import mouse_state


class Slider(Sprite):
    def __init__(
        self,
        min_value=0,
        max_value=100,
        value=50,
        x=0,
        y=0,
        width=200,
        height=20,
        track_color="lightgray",
        fill_color="royalblue",
        thumb_color="royalblue",
        thumb_radius=12,
        border_radius=10,
        transparency=100,
        anchor=None,
        layer=10,
        disabled=False,
        show_value=False,
        font_size=16,
        font=None,
        value_color="black",
        step=None,
    ):
        self._min_value = min_value
        self._max_value = max_value
        self._value = max(min_value, min(max_value, value))
        self._width = width
        self._height = height
        self._track_color = track_color
        self._fill_color = fill_color
        self._thumb_color = thumb_color
        self._thumb_radius = thumb_radius
        self._border_radius = border_radius
        self._transparency = transparency
        self._size = 100
        self._angle = 0
        self._is_disabled = disabled
        self._dragging = False
        self._show_value = show_value
        self._slider_font = _load_font(font, font_size)
        self._slider_font_size = font_size
        self._slider_font_path = font
        self._value_color = value_color
        self._step = step
        self._on_change_callbacks = []
        self._image = None
        self.rect = pygame.Rect(0, 0, 0, 0)
        super().__init__(x=x, y=y, anchor=anchor, layer=layer)
        self.update()

    def update(self):
        """Handle drag input then re-render."""
        if not self._is_disabled:
            touching = mouse.is_touching(self)
            if mouse_state.click_happened and touching:
                self._dragging = True
            if not mouse._is_clicked:
                self._dragging = False
            if self._dragging:
                self._update_value_from_mouse()
        super().update()

    def _update_value_from_mouse(self):
        """Compute the slider value from the current mouse x position."""
        # Track left/right edges in pygame screen space
        pos = convert_pos(self.x, self.y)
        track_left = pos[0] - self._width // 2 + self._thumb_radius
        track_right = pos[0] + self._width // 2 - self._thumb_radius
        track_width = track_right - track_left

        # Mouse x in pygame screen coords
        mouse_px = mouse.x + screen.width / 2.0

        t = (mouse_px - track_left) / track_width if track_width > 0 else 0
        t = max(0.0, min(1.0, t))
        raw = self._min_value + t * (self._max_value - self._min_value)

        if self._step is not None and self._step > 0:
            raw = round(raw / self._step) * self._step

        new_val = max(self._min_value, min(self._max_value, raw))
        if new_val != self._value:
            self._value = new_val
            self._should_recompute = True
            for cb in self._on_change_callbacks:
                cb(self._value)

    def _render(self):
        """Draw the track, filled portion, and thumb circle."""
        w, h = self._width, self._height
        canvas_h = h + self._thumb_radius * 2
        draw_image = pygame.Surface((w, canvas_h), pygame.SRCALPHA)

        cy = canvas_h // 2  # vertical centre

        # Track background
        track_rect = pygame.Rect(0, cy - h // 2, w, h)
        pygame.draw.rect(
            draw_image,
            _color_name_to_rgb(self._track_color),
            track_rect,
            border_radius=self._border_radius,
        )

        # Filled portion — fill ends at the thumb centre so both use the same formula
        t = (self._value - self._min_value) / max(1, self._max_value - self._min_value)
        thumb_x = int(t * (w - 2 * self._thumb_radius)) + self._thumb_radius
        if thumb_x > 0:
            fill_rect = pygame.Rect(0, cy - h // 2, thumb_x, h)
            pygame.draw.rect(
                draw_image,
                _color_name_to_rgb(self._fill_color),
                fill_rect,
                border_radius=self._border_radius,
            )

        # Thumb
        pygame.draw.circle(
            draw_image,
            _color_name_to_rgb(self._thumb_color),
            (thumb_x, cy),
            self._thumb_radius,
        )

        # Dim when disabled
        if self._is_disabled:
            overlay = pygame.Surface((w, canvas_h), pygame.SRCALPHA)
            overlay.fill((200, 200, 200, 120))
            draw_image.blit(overlay, (0, 0))

        # Value label
        if self._show_value:
            label = (
                str(int(self._value))
                if isinstance(self._value, float) and self._value == int(self._value)
                else str(self._value)
            )
            label_surf = self._slider_font.render(
                label, True, _color_name_to_rgb(self._value_color)
            )
            draw_image.blit(label_surf, (w + 6, cy - label_surf.get_height() // 2))

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
        """The current slider value (between min_value and max_value)."""
        return self._value

    @value.setter
    def value(self, v):
        self._value = max(self._min_value, min(self._max_value, v))
        self._should_recompute = True
        for cb in self._on_change_callbacks:
            cb(self._value)

    @property
    def min_value(self):
        """The minimum value of the slider range."""
        return self._min_value

    @min_value.setter
    def min_value(self, v):
        self._min_value = v
        self._value = max(v, self._value)
        self._should_recompute = True

    @property
    def max_value(self):
        """The maximum value of the slider range."""
        return self._max_value

    @max_value.setter
    def max_value(self, v):
        self._max_value = v
        self._value = min(v, self._value)
        self._should_recompute = True

    @property
    def disabled(self):
        """Whether the slider is non-interactive."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, v):
        self._is_disabled = bool(v)
        self._should_recompute = True

    def when_changed(self, func):
        """Decorator — *func(value)* is called whenever the slider moves."""
        if _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} is async. when_changed callbacks must be regular functions."
            )
        self._on_change_callbacks.append(func)
        return func

    def clone(self):
        return Slider(
            min_value=self._min_value,
            max_value=self._max_value,
            value=self._value,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            width=self._width,
            height=self._height,
            track_color=self._track_color,
            fill_color=self._fill_color,
            thumb_color=self._thumb_color,
            thumb_radius=self._thumb_radius,
            border_radius=self._border_radius,
            transparency=self._transparency,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
            show_value=self._show_value,
            font_size=self._slider_font_size,
            font=self._slider_font_path,
            value_color=self._value_color,
            step=self._step,
        )
