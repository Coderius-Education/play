"""Dropdown — a button that reveals a list of selectable options."""

import math as _math
import pygame

from .box import Box
from ..io.mouse import mouse
from ..utils import (
    color_name_to_rgb as _color_name_to_rgb,
    load_font as _load_font,
    reject_async_callback as _reject_async,
)
from ..io.screen import convert_pos
from ..core.mouse_loop import mouse_state


class Dropdown(Box):
    """A dropdown/select widget.

    When closed the widget renders as a single-row button showing the current
    selection.  When open, it expands downward to show all options.  Clicking
    an option selects it and closes the menu.

    The open menu is rendered as an extension of the sprite's own image so
    it works within the existing pygame sprite layer system.
    """

    def __init__(
        self,
        options=None,
        selected_index=0,
        x=0,
        y=0,
        width=160,
        height=40,
        color="white",
        hover_color="lightyellow",
        option_hover_color="cornflowerblue",
        text_color="black",
        border_color="gray",
        border_width=1,
        border_radius=4,
        font_size=18,
        font=None,
        transparency=100,
        anchor=None,
        layer=20,
        disabled=False,
        placeholder="Select…",
    ):
        self._options = list(options) if options else []
        self._selected_index = selected_index if self._options else -1
        self._dropdown_open = False
        self._hover_color = hover_color
        self._option_hover_color = option_hover_color
        self._text_color = text_color
        self._base_color = color
        self._dropdown_font = _load_font(font, font_size)
        self._dropdown_font_size = font_size
        self._dropdown_font_path = font
        self._on_change_callbacks = []
        self._is_disabled = disabled
        self._placeholder = placeholder
        self._hovered_option = -1  # which option row the mouse is over

        super().__init__(
            color=color,
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

    def update(self):
        """Handle clicks on the button and on the open option list."""
        if not self._is_disabled:
            if mouse_state.click_happened:
                # Check if click lands on the open option list
                if self._dropdown_open and self._hovered_option >= 0:
                    self._select(self._hovered_option)
                    self._dropdown_open = False
                    self._should_recompute = True
                elif mouse.is_touching(self):
                    self._dropdown_open = not self._dropdown_open
                    self._should_recompute = True
                elif self._dropdown_open:
                    # Click outside: close the menu
                    self._dropdown_open = False
                    self._should_recompute = True

            # Track which option row the mouse is hovering over
            if self._dropdown_open:
                old_hover = self._hovered_option
                self._hovered_option = self._option_at_mouse()
                if self._hovered_option != old_hover:
                    self._should_recompute = True

        self._color = (
            self._hover_color
            if mouse.is_touching(self) and not self._dropdown_open
            else self._base_color
        )
        super().update()

    def _option_at_mouse(self):
        """Return the index of the option row under the mouse, or -1."""
        pos = convert_pos(self.x, self.y)
        closed_top = pos[1] - self._height // 2
        option_top = pos[0] - self._width // 2
        option_right = pos[0] + self._width // 2

        mouse_px, mouse_py = convert_pos(mouse.x, mouse.y)

        if not option_top <= mouse_px <= option_right:
            return -1

        for i, _ in enumerate(self._options):
            row_y = closed_top + self._height * (i + 1)
            if row_y <= mouse_py < row_y + self._height:
                return i
        return -1

    def _select(self, index):
        self._selected_index = index
        self._should_recompute = True
        val = self._options[index] if index < len(self._options) else None
        for cb in self._on_change_callbacks:
            cb(val, index)

    def _render(self):
        """Draw the closed button plus the open option list (if open)."""
        n_extra = len(self._options) if self._dropdown_open else 0
        total_h = self._height * (1 + n_extra)
        w = self._width
        bw = self._border_width

        draw_image = pygame.Surface((w, total_h), pygame.SRCALPHA)

        # ── closed button row ──────────────────────────────────────────────
        btn_rect = pygame.Rect(0, 0, w, self._height)
        if bw > 0:
            pygame.draw.rect(
                draw_image,
                _color_name_to_rgb(self._border_color),
                btn_rect,
                bw,
                border_radius=self._border_radius,
            )
        pygame.draw.rect(
            draw_image,
            _color_name_to_rgb(self._color),
            (bw, bw, w - 2 * bw, self._height - 2 * bw),
            border_radius=max(0, self._border_radius - bw),
        )

        # Selected label or placeholder
        label = (
            str(self._options[self._selected_index])
            if 0 <= self._selected_index < len(self._options)
            else self._placeholder
        )
        label_surf = self._dropdown_font.render(
            label, True, _color_name_to_rgb(self._text_color)
        )
        ly = (self._height - label_surf.get_height()) // 2
        draw_image.blit(label_surf, (bw + 8, ly))

        # Arrow indicator (▼ / ▲)
        arrow = "▲" if self._dropdown_open else "▼"
        arrow_surf = self._dropdown_font.render(
            arrow, True, _color_name_to_rgb(self._text_color)
        )
        draw_image.blit(arrow_surf, (w - arrow_surf.get_width() - 8, ly))

        # ── open option rows ───────────────────────────────────────────────
        if self._dropdown_open:
            for i, option in enumerate(self._options):
                row_y = self._height * (i + 1)
                row_rect = pygame.Rect(0, row_y, w, self._height)

                bg = (
                    _color_name_to_rgb(self._option_hover_color)
                    if i == self._hovered_option
                    else _color_name_to_rgb(self._base_color)
                )
                if bw > 0:
                    pygame.draw.rect(
                        draw_image,
                        _color_name_to_rgb(self._border_color),
                        row_rect,
                        bw,
                    )
                pygame.draw.rect(
                    draw_image,
                    bg,
                    (bw, row_y + bw, w - 2 * bw, self._height - 2 * bw),
                )
                opt_surf = self._dropdown_font.render(
                    str(option), True, _color_name_to_rgb(self._text_color)
                )
                oly = row_y + (self._height - opt_surf.get_height()) // 2
                draw_image.blit(opt_surf, (bw + 8, oly))

        if self._is_disabled:
            self._draw_disabled_overlay(draw_image)

        draw_image.set_alpha(round(self._transparency * 255 / 100))

        # Position: the closed button stays centred at the play-coordinate y and
        # the option list expands downward. The image (which may be taller than
        # the button when open) blits from rect.topleft, so we keep rect.height
        # at the *closed* height — otherwise _apply_anchor would re-anchor using
        # the full open height and an edge-anchored dropdown would jump when it
        # opens.
        pos = convert_pos(self.x, self.y)
        angle_deg = _math.degrees(self.physics._pymunk_body.angle)
        self.image = pygame.transform.rotate(draw_image, angle_deg)
        self.rect = self.image.get_rect(
            center=(pos[0], pos[1] - self._height // 2 + total_h // 2)
        )
        self.rect.height = self._height
        self.rect.top = pos[1] - self._height // 2

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def selected_value(self):
        """The currently selected option, or None."""
        if 0 <= self._selected_index < len(self._options):
            return self._options[self._selected_index]
        return None

    @property
    def selected_index(self):
        """The index of the selected option (-1 = nothing selected)."""
        return self._selected_index

    @selected_index.setter
    def selected_index(self, v):
        self._selected_index = max(-1, min(len(self._options) - 1, v))
        self._should_recompute = True

    @property
    def options(self):
        """The list of selectable options."""
        return list(self._options)

    @options.setter
    def options(self, v):
        self._options = list(v)
        if self._selected_index >= len(self._options):
            self._selected_index = len(self._options) - 1
        self._should_recompute = True

    @property
    def is_open(self):
        """Whether the dropdown is currently expanded."""
        return self._dropdown_open

    @property
    def disabled(self):
        """Whether the dropdown is non-interactive."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, v):
        self._is_disabled = bool(v)
        if v:
            self._dropdown_open = False
        self._should_recompute = True

    def when_changed(self, func):
        """Decorator — *func(value, index)* is called when the selection changes."""
        _reject_async(func, "when_changed")
        self._on_change_callbacks.append(func)
        return func

    def clone(self):
        return Dropdown(
            options=list(self._options),
            selected_index=self._selected_index,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            width=self._width,
            height=self._height,
            color=self._base_color,
            hover_color=self._hover_color,
            option_hover_color=self._option_hover_color,
            text_color=self._text_color,
            border_color=self._border_color,
            border_width=self._border_width,
            border_radius=self._border_radius,
            font_size=self._dropdown_font_size,
            font=self._dropdown_font_path,
            transparency=self._transparency,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
            placeholder=self._placeholder,
        )
