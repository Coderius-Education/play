"""Checkbox — a toggleable Boolean control with an optional text label."""

import pygame

from .box import Box
from ..io.mouse import mouse
from ..utils import (
    color_name_to_rgb as _color_name_to_rgb,
    load_font as _load_font,
    reject_async_callback as _reject_async,
)
from ..core.mouse_loop import mouse_state


class Checkbox(Box):
    def __init__(
        self,
        label="",
        checked=False,
        x=0,
        y=0,
        size_px=24,
        color="white",
        check_color="royalblue",
        border_color="darkgray",
        hover_border_color="steelblue",
        label_color="black",
        font_size=18,
        font=None,
        border_radius=4,
        transparency=100,
        anchor=None,
        layer=10,
        disabled=False,
    ):
        self._checked = checked
        self._check_color = check_color
        self._label_text = label
        self._label_color = label_color
        self._hover_border_color = hover_border_color
        self._checkbox_font = _load_font(font, font_size)
        self._checkbox_font_size = font_size
        self._checkbox_font_path = font
        self._is_disabled = disabled
        self._was_hovered = False
        self._on_change_callbacks = []

        # Width includes the box + label area
        label_w = self._checkbox_font.size(label)[0] if label else 0
        total_w = size_px + (10 + label_w if label else 0)

        super().__init__(
            color=color,
            x=x,
            y=y,
            width=total_w,
            height=size_px,
            border_color=border_color,
            border_width=2,
            border_radius=border_radius,
            transparency=transparency,
            anchor=anchor,
            layer=layer,
        )

    def update(self):
        """Toggle checked state on click; re-render on hover changes."""
        hovered = mouse.is_touching(self)
        if not self._is_disabled and mouse_state.click_happened and hovered:
            self._checked = not self._checked
            self._should_recompute = True
            for cb in self._on_change_callbacks:
                cb(self._checked)
        # Hover border is computed in _render(); mark dirty when hover changes so
        # the border actually reacts to the mouse entering/leaving.
        if hovered != self._was_hovered:
            self._was_hovered = hovered
            self._should_recompute = True
        super().update()

    def _render(self):
        """Draw the checkbox box, checkmark, and label."""
        size_px = self._height
        draw_image = pygame.Surface((self._width, self._height), pygame.SRCALPHA)

        border_col = (
            _color_name_to_rgb(self._border_color)
            if not mouse.is_touching(self)
            else _color_name_to_rgb(self._hover_border_color)
        )

        # Background square
        pygame.draw.rect(
            draw_image,
            _color_name_to_rgb(self._color),
            (0, 0, size_px, size_px),
            border_radius=self._border_radius,
        )
        # Border
        pygame.draw.rect(
            draw_image,
            border_col,
            (0, 0, size_px, size_px),
            self._border_width,
            border_radius=self._border_radius,
        )

        # Checkmark (filled square or tick)
        if self._checked:
            inner = 5
            pygame.draw.rect(
                draw_image,
                _color_name_to_rgb(self._check_color),
                (inner, inner, size_px - 2 * inner, size_px - 2 * inner),
                border_radius=max(0, self._border_radius - 2),
            )

        # Dim when disabled
        if self._is_disabled:
            self._draw_disabled_overlay(draw_image)

        # Label text
        if self._label_text:
            label_surf = self._checkbox_font.render(
                self._label_text, True, _color_name_to_rgb(self._label_color)
            )
            ly = (self._height - label_surf.get_height()) // 2
            draw_image.blit(label_surf, (size_px + 10, ly))

        self._finalize_image(draw_image)

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def checked(self):
        """Whether the checkbox is currently checked."""
        return self._checked

    @checked.setter
    def checked(self, value):
        self._checked = bool(value)
        self._should_recompute = True

    @property
    def label(self):
        """The label text shown next to the checkbox."""
        return self._label_text

    @label.setter
    def label(self, value):
        self._label_text = value
        self._should_recompute = True

    @property
    def disabled(self):
        """Whether the checkbox is non-interactive."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, value):
        self._is_disabled = bool(value)
        self._should_recompute = True

    def when_changed(self, func):
        """Decorator — *func(checked: bool)* is called when the state toggles."""
        _reject_async(func, "when_changed")
        self._on_change_callbacks.append(func)
        return func

    def clone(self):
        return Checkbox(
            label=self._label_text,
            checked=self._checked,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            size_px=self._height,
            color=self._color,
            check_color=self._check_color,
            border_color=self._border_color,
            hover_border_color=self._hover_border_color,
            label_color=self._label_color,
            font_size=self._checkbox_font_size,
            font=self._checkbox_font_path,
            border_radius=self._border_radius,
            transparency=self._transparency,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
        )
