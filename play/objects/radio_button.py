"""RadioButton and RadioGroup — mutually exclusive selection controls."""

import pygame

from .sprite import Sprite
from ..io.mouse import mouse
from ..utils import (
    color_name_to_rgb as _color_name_to_rgb,
    load_font as _load_font,
    reject_async_callback as _reject_async,
)
from ..core.mouse_loop import mouse_state


class RadioGroup:
    """Manages a set of RadioButtons so only one can be selected at a time."""

    def __init__(self):
        self._buttons = []
        self._on_change_callbacks = []

    def _register(self, button):
        self._buttons.append(button)

    def _unregister(self, button):
        try:
            self._buttons.remove(button)
        except ValueError:
            pass

    def _select(self, selected_button):
        """Called by a RadioButton when it is clicked; deselects all others."""
        for btn in self._buttons:
            if btn is not selected_button:
                btn._selected = False
                btn._should_recompute = True
        selected_button._selected = True
        selected_button._should_recompute = True
        for cb in self._on_change_callbacks:
            cb(selected_button.value)

    @property
    def selected_value(self):
        """The value of the currently selected RadioButton, or None."""
        for btn in self._buttons:
            if btn._selected:
                return btn.value
        return None

    @selected_value.setter
    def selected_value(self, v):
        """Select the RadioButton with the given value.

        Fires ``when_changed`` when a matching option exists (consistent with a
        click). If no option matches, the selection is cleared and no callback
        fires — there is no selected value to report."""
        for btn in self._buttons:
            if btn.value == v:
                self._select(btn)
                return
        for btn in self._buttons:
            btn._selected = False
            btn._should_recompute = True

    def when_changed(self, func):
        """Decorator — *func(value)* is called when selection changes."""
        _reject_async(func, "when_changed")
        self._on_change_callbacks.append(func)
        return func


class RadioButton(Sprite):
    def __init__(
        self,
        label="",
        value="",
        group=None,
        x=0,
        y=0,
        size_px=22,
        color="white",
        selected_color="royalblue",
        border_color="darkgray",
        hover_border_color="steelblue",
        label_color="black",
        font_size=18,
        font=None,
        transparency=100,
        anchor=None,
        layer=10,
        disabled=False,
        selected=False,
    ):
        self._label_text = label
        self._value = value
        self._group = group
        self._size_px = size_px
        self._radio_color = color
        self._selected_color = selected_color
        self._border_color = border_color
        self._hover_border_color = hover_border_color
        self._label_color = label_color
        self._radio_font = _load_font(font, font_size)
        self._radio_font_size = font_size
        self._radio_font_path = font
        self._transparency = transparency
        self._size = 100
        self._angle = 0
        self._is_disabled = disabled
        self._selected = selected
        self._hovered = False  # cached hover state (never True while disabled)
        self._image = None
        # Seed the rect with the real widget size so the pymunk hit-shape is
        # built correctly (a 0x0 rect yields a degenerate point shape that makes
        # clicks miss or bleed between stacked radios).
        label_w = self._radio_font.size(label)[0] if label else 0
        w = size_px + (10 + label_w if label else 0)
        self.rect = pygame.Rect(0, 0, w, size_px)

        if group is not None:
            group._register(self)
            if selected:
                # Enforce the group's single-selection invariant: deselect the
                # siblings directly (not via group._select, which would fire
                # when_changed callbacks for a construction-time default).
                for btn in group._buttons:
                    if btn is not self:
                        btn._selected = False
                        btn._should_recompute = True

        super().__init__(x=x, y=y, anchor=anchor, layer=layer)
        self.update()

    def update(self):
        """Handle click to select; re-render on hover changes."""
        # Disabled widgets never show hover feedback.
        hovered = not self._is_disabled and mouse.is_touching(self)
        if mouse_state.click_happened and hovered:
            if self._group is not None:
                self._group._select(self)
            else:
                self._selected = True
                self._should_recompute = True
        # Hover border is drawn in _render() from the cached value; mark dirty
        # when hover changes so the border reacts to the mouse entering/leaving.
        if hovered != self._hovered:
            self._hovered = hovered
            self._should_recompute = True
        super().update()

    def _render(self):
        """Draw radio circle and label."""
        r = self._size_px // 2
        label_w = self._radio_font.size(self._label_text)[0] if self._label_text else 0
        w = self._size_px + (10 + label_w if self._label_text else 0)
        h = self._size_px
        draw_image = pygame.Surface((w, h), pygame.SRCALPHA)

        cx, cy = r, r
        border_col = (
            _color_name_to_rgb(self._hover_border_color)
            if self._hovered
            else _color_name_to_rgb(self._border_color)
        )

        # Outer circle
        pygame.draw.circle(
            draw_image, _color_name_to_rgb(self._radio_color), (cx, cy), r
        )
        pygame.draw.circle(draw_image, border_col, (cx, cy), r, 2)

        # Inner filled dot when selected
        if self._selected:
            inner_r = max(1, r - 5)
            pygame.draw.circle(
                draw_image, _color_name_to_rgb(self._selected_color), (cx, cy), inner_r
            )

        # Dim when disabled
        if self._is_disabled:
            self._draw_disabled_overlay(draw_image)

        # Label
        if self._label_text:
            label_surf = self._radio_font.render(
                self._label_text, True, _color_name_to_rgb(self._label_color)
            )
            ly = (h - label_surf.get_height()) // 2
            draw_image.blit(label_surf, (self._size_px + 10, ly))

        self._finalize_image(draw_image)

    # ── public API ────────────────────────────────────────────────────────────

    @property
    def value(self):
        """The value associated with this radio button."""
        return self._value

    @property
    def selected(self):
        """Whether this radio button is currently selected."""
        return self._selected

    @selected.setter
    def selected(self, v):
        if self._group is not None and v:
            self._group._select(self)
        else:
            self._selected = bool(v)
            self._should_recompute = True

    @property
    def label(self):
        """The text label shown beside the radio button."""
        return self._label_text

    @label.setter
    def label(self, v):
        self._label_text = v
        # Resize the hit-shape to match the new label width (the shape is built
        # from self.rect, which otherwise stays frozen at the old label size).
        label_w = self._radio_font.size(v)[0] if v else 0
        w = self._size_px + (10 + label_w if v else 0)
        self.rect = pygame.Rect(self.rect.x, self.rect.y, w, self._size_px)
        self.physics._remove()
        self.physics._make_pymunk()
        self._should_recompute = True

    @property
    def disabled(self):
        """Whether the radio button is non-interactive."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, v):
        self._is_disabled = bool(v)
        self._should_recompute = True

    def remove(self):
        if self._group is not None:
            self._group._unregister(self)
        super().remove()

    def clone(self):
        return RadioButton(
            label=self._label_text,
            value=self._value,
            group=self._group,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            size_px=self._size_px,
            color=self._radio_color,
            selected_color=self._selected_color,
            border_color=self._border_color,
            hover_border_color=self._hover_border_color,
            label_color=self._label_color,
            font_size=self._radio_font_size,
            font=self._radio_font_path,
            transparency=self._transparency,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
            selected=self._selected,
        )
