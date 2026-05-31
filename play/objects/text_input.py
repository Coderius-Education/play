"""TextInput — a clickable, keyboard-editable text field widget."""

import inspect as _inspect
import pygame

from .box import Box
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb
from . import text_input_registry as _registry
from ..core.mouse_loop import mouse_state


class TextInput(Box):
    def __init__(
        self,
        placeholder="",
        value="",
        x=0,
        y=0,
        width=200,
        height=40,
        color="white",
        active_color="lightyellow",
        text_color="black",
        placeholder_color="gray",
        font_size=20,
        border_color="gray",
        border_width=1,
        border_radius=4,
        max_length=None,
        transparency=100,
        size=100,
        anchor=None,
        layer=10,
    ):
        self._input_value = value
        self._placeholder = placeholder
        self._active_color = active_color
        self._base_input_color = color
        self._text_color = text_color
        self._placeholder_color = placeholder_color
        self._input_font_size = font_size
        self._input_font = pygame.font.SysFont(None, font_size)
        self._max_length = max_length
        self._is_focused = False
        self._cursor_visible = True
        self._last_blink = 0
        self._on_change_callbacks = []
        self._on_submit_callbacks = []
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
            size=size,
            anchor=anchor,
            layer=layer,
        )

    def update(self):
        """Handle focus, cursor blink, box rendering, and text overlay."""
        if mouse_state.click_happened:
            if mouse.is_touching(self):
                if not self._is_focused:
                    _registry.focus(self)
                    self._cursor_visible = True
                    self._last_blink = pygame.time.get_ticks()
            elif self._is_focused:
                _registry.clear_focus()

        if self._is_focused:
            now = pygame.time.get_ticks()
            if now - self._last_blink >= 500:
                self._last_blink = now
                self._cursor_visible = not self._cursor_visible
                self._should_recompute = True

        self._color = self._active_color if self._is_focused else self._base_input_color
        super().update()

    def _render(self):
        """Draw box background then blit text/cursor on top."""
        super()._render()  # Box._render()
        self._blit_input_text()

    def _handle_text_input(self, text):
        """Append *text* (from a TEXTINPUT pygame event) to the current value."""
        if self._max_length is not None:
            remaining = self._max_length - len(self._input_value)
            if remaining <= 0:
                return
            text = text[:remaining]
        self._input_value += text
        self._cursor_visible = True
        self._last_blink = pygame.time.get_ticks()
        self._should_recompute = True
        for cb in self._on_change_callbacks:
            cb(self._input_value)

    def _handle_keydown(self, event):
        """Handle backspace, enter, and escape from a KEYDOWN pygame event."""
        if event.key == pygame.K_BACKSPACE:
            if self._input_value:
                self._input_value = self._input_value[:-1]
                self._cursor_visible = True
                self._last_blink = pygame.time.get_ticks()
                self._should_recompute = True
                for cb in self._on_change_callbacks:
                    cb(self._input_value)
        elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            for cb in self._on_submit_callbacks:
                cb(self._input_value)
        elif event.key == pygame.K_ESCAPE:
            _registry.clear_focus()

    def _blit_input_text(self):
        """Draw the value (or placeholder) and cursor onto the rendered box image."""
        font = self._input_font
        padding = 8

        if self._input_value:
            display = self._input_value
            text_color = _color_name_to_rgb(self._text_color)
        elif not self._is_focused and self._placeholder:
            display = self._placeholder
            text_color = _color_name_to_rgb(self._placeholder_color)
        else:
            display = ""
            text_color = _color_name_to_rgb(self._text_color)

        if self._is_focused and self._cursor_visible:
            display += "|"

        if not display:
            return

        text_surf = font.render(display, True, text_color)
        y_pos = (self.image.get_height() - text_surf.get_height()) // 2
        max_w = self.image.get_width() - 2 * padding

        if text_surf.get_width() > max_w:
            # Scroll to the end: show the rightmost portion that fits
            src_rect = pygame.Rect(
                text_surf.get_width() - max_w, 0, max_w, text_surf.get_height()
            )
            self.image.blit(text_surf, (padding, y_pos), src_rect)
        else:
            self.image.blit(text_surf, (padding, y_pos))

    # ── public API ──────────────────────────────────────────────────────────

    @property
    def value(self):
        """The current text value of the input."""
        return self._input_value

    @value.setter
    def value(self, new_value):
        """Set the text value programmatically. Fires when_changed callbacks."""
        self._input_value = str(new_value)
        self._should_recompute = True
        for cb in self._on_change_callbacks:
            cb(self._input_value)

    @property
    def placeholder(self):
        """The hint text shown when the field is empty and unfocused."""
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value):
        self._placeholder = value
        self._should_recompute = True

    @property
    def text_color(self):
        """The colour of the typed text."""
        return self._text_color

    @text_color.setter
    def text_color(self, value):
        self._text_color = value
        self._should_recompute = True

    @property
    def placeholder_color(self):
        """The colour of the placeholder text."""
        return self._placeholder_color

    @placeholder_color.setter
    def placeholder_color(self, value):
        self._placeholder_color = value
        self._should_recompute = True

    @property
    def font_size(self):
        """The font size used for text rendering."""
        return self._input_font_size

    @font_size.setter
    def font_size(self, value):
        self._input_font_size = value
        self._input_font = pygame.font.SysFont(None, value)
        self._should_recompute = True

    def when_changed(self, func):
        """Decorator — *func(value)* is called whenever the text changes."""
        if _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} is async. when_changed callbacks must be regular functions."
            )
        self._on_change_callbacks.append(func)
        return func

    def when_submit(self, func):
        """Decorator — *func(value)* is called when the user presses Enter."""
        if _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} is async. when_submit callbacks must be regular functions."
            )
        self._on_submit_callbacks.append(func)
        return func

    def clone(self):
        """Create a copy of this text input (value and focus state are not copied)."""
        return TextInput(
            placeholder=self._placeholder,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            width=self._width,
            height=self._height,
            color=self._base_input_color,
            active_color=self._active_color,
            text_color=self._text_color,
            placeholder_color=self._placeholder_color,
            font_size=self._input_font_size,
            border_color=self._border_color,
            border_width=self._border_width,
            border_radius=self._border_radius,
            max_length=self._max_length,
            transparency=self._transparency,
            size=self._size,
            anchor=self._anchor,
            layer=self._layer,
        )

    def remove(self):
        if self._is_focused:
            _registry.clear_focus()
        super().remove()
