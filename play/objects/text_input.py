"""TextInput — a clickable, keyboard-editable text field widget."""

import inspect as _inspect
from typing import Optional as _Optional

import pygame

from .box import Box
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb, load_font as _load_font
from . import text_input_registry as _registry
from ..core.mouse_loop import mouse_state


class TextInput(Box):
    # character used for password masking
    _MASK_CHAR = "•"  # •

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
        font=None,
        border_color="gray",
        border_width=1,
        border_radius=4,
        max_length: _Optional[int] = None,
        transparency=100,
        size=100,
        anchor=None,
        layer=10,
        disabled=False,
        readonly=False,
        password_mode=False,
    ):
        self._input_value = value
        self._placeholder = placeholder
        self._active_color = active_color
        self._base_input_color = color
        self._text_color = text_color
        self._placeholder_color = placeholder_color
        self._input_font_size = font_size
        self._input_font_path = font
        self._input_font = _load_font(font, font_size)
        self._max_length = max_length
        self._is_focused = False
        self._cursor_visible = True
        self._last_blink = 0
        self._cursor_pos = len(value)  # index into _input_value
        self._selection_start = None  # None = no selection
        self._selection_end = None
        self._on_change_callbacks = []
        self._on_submit_callbacks = []
        self._is_disabled = disabled
        self._readonly = readonly
        self._password_mode = password_mode
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
        _registry.register(self)

    def update(self):
        """Handle focus, cursor blink, box rendering, and text overlay."""
        if not self._is_disabled and mouse_state.click_happened:
            if mouse.is_touching(self):
                if not self._is_focused:
                    _registry.focus(self)
                    self._cursor_visible = True
                    self._last_blink = pygame.time.get_ticks()
                    self._cursor_pos = len(self._input_value)
                    self._selection_start = self._selection_end = None
            elif self._is_focused:
                _registry.clear_focus()

        if self._is_focused:
            now = pygame.time.get_ticks()
            if now - self._last_blink >= 500:
                self._last_blink = now
                self._cursor_visible = not self._cursor_visible
                self._should_recompute = True

        if self._is_disabled:
            self._color = self._base_input_color
        else:
            self._color = (
                self._active_color if self._is_focused else self._base_input_color
            )
        super().update()

    def _render(self):
        """Draw box background then blit text/cursor on top."""
        super()._render()  # Box._render()
        self._blit_input_text()

    # ── keyboard event handlers ───────────────────────────────────────────────

    def _handle_text_input(self, text):
        """Append *text* (from a TEXTINPUT pygame event) to the current value."""
        if self._readonly or self._is_disabled:
            return
        if self._selection_start is not None:
            self._delete_selection()
        if self._max_length is not None:
            remaining = self._max_length - len(self._input_value)
            if remaining <= 0:
                return
            text = text[:remaining]
        self._input_value = (
            self._input_value[: self._cursor_pos]
            + text
            + self._input_value[self._cursor_pos :]
        )
        self._cursor_pos += len(text)
        self._cursor_visible = True
        self._last_blink = pygame.time.get_ticks()
        self._should_recompute = True
        for cb in self._on_change_callbacks:
            cb(self._input_value)

    def _handle_keydown(
        self, event
    ):  # pylint: disable=too-many-return-statements,too-many-branches,too-many-statements
        """Handle navigation, editing, clipboard, and Tab keys from a KEYDOWN event."""
        mods = pygame.key.get_mods()
        ctrl = mods & (pygame.KMOD_CTRL | pygame.KMOD_META)

        if event.key == pygame.K_TAB:
            _registry.focus_next()
            return

        if event.key == pygame.K_ESCAPE:
            _registry.clear_focus()
            return

        if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            for cb in self._on_submit_callbacks:
                cb(self._input_value)
            return

        # Navigation
        if event.key == pygame.K_LEFT:
            if self._cursor_pos > 0:
                self._cursor_pos -= 1
                self._selection_start = self._selection_end = None
                self._cursor_visible = True
                self._should_recompute = True
            return

        if event.key == pygame.K_RIGHT:
            if self._cursor_pos < len(self._input_value):
                self._cursor_pos += 1
                self._selection_start = self._selection_end = None
                self._cursor_visible = True
                self._should_recompute = True
            return

        if event.key == pygame.K_HOME:
            self._cursor_pos = 0
            self._selection_start = self._selection_end = None
            self._cursor_visible = True
            self._should_recompute = True
            return

        if event.key == pygame.K_END:
            self._cursor_pos = len(self._input_value)
            self._selection_start = self._selection_end = None
            self._cursor_visible = True
            self._should_recompute = True
            return

        # Editing is blocked for readonly/disabled
        if self._readonly or self._is_disabled:
            return

        if ctrl and event.key == pygame.K_a:
            self._selection_start = 0
            self._selection_end = len(self._input_value)
            self._cursor_pos = len(self._input_value)
            self._should_recompute = True
            return

        if ctrl and event.key == pygame.K_c:
            selected = self._get_selected_text()
            if selected:
                pygame.scrap.init()
                pygame.scrap.put_text(selected)
            return

        if ctrl and event.key == pygame.K_x:
            selected = self._get_selected_text()
            if selected:
                pygame.scrap.init()
                pygame.scrap.put_text(selected)
                self._delete_selection()
                self._fire_change()
            return

        if ctrl and event.key == pygame.K_v:
            try:
                pygame.scrap.init()
                pasted = pygame.scrap.get_text()
                if pasted:
                    if self._selection_start is not None:
                        self._delete_selection()
                    if self._max_length is not None:
                        remaining = self._max_length - len(self._input_value)
                        pasted = pasted[:remaining]
                    self._input_value = (
                        self._input_value[: self._cursor_pos]
                        + pasted
                        + self._input_value[self._cursor_pos :]
                    )
                    self._cursor_pos += len(pasted)
                    self._selection_start = self._selection_end = None
                    self._fire_change()
            except (
                pygame.error,
                OSError,
                ValueError,
            ):  # scrap not available in all environments
                pass
            return

        if event.key == pygame.K_BACKSPACE:
            if self._selection_start is not None:
                self._delete_selection()
                self._fire_change()
            elif self._cursor_pos > 0:
                self._input_value = (
                    self._input_value[: self._cursor_pos - 1]
                    + self._input_value[self._cursor_pos :]
                )
                self._cursor_pos -= 1
                self._cursor_visible = True
                self._last_blink = pygame.time.get_ticks()
                self._should_recompute = True
                self._fire_change()
            return

        if event.key == pygame.K_DELETE:
            if self._selection_start is not None:
                self._delete_selection()
                self._fire_change()
            elif self._cursor_pos < len(self._input_value):
                self._input_value = (
                    self._input_value[: self._cursor_pos]
                    + self._input_value[self._cursor_pos + 1 :]
                )
                self._cursor_visible = True
                self._should_recompute = True
                self._fire_change()

    # ── selection helpers ─────────────────────────────────────────────────────

    def _get_selected_text(self):
        if self._selection_start is None:
            return ""
        a = min(self._selection_start, self._selection_end)
        b = max(self._selection_start, self._selection_end)
        return self._input_value[a:b]

    def _delete_selection(self):
        a = min(self._selection_start, self._selection_end)
        b = max(self._selection_start, self._selection_end)
        self._input_value = self._input_value[:a] + self._input_value[b:]
        self._cursor_pos = a
        self._selection_start = self._selection_end = None
        self._should_recompute = True

    def _fire_change(self):
        for cb in self._on_change_callbacks:
            cb(self._input_value)

    # ── rendering ─────────────────────────────────────────────────────────────

    def _display_text(self, value):
        """Return the string to render (masked in password mode)."""
        if self._password_mode:
            return self._MASK_CHAR * len(value)
        return value

    def _blit_input_text(self):  # pylint: disable=too-many-statements
        """Draw the value (or placeholder) and cursor onto the rendered box image."""
        font = self._input_font
        padding = 8

        has_value = bool(self._input_value)
        if has_value:
            display = self._display_text(self._input_value)
            text_color = _color_name_to_rgb(self._text_color)
        elif not self._is_focused and self._placeholder:
            display = self._placeholder
            text_color = _color_name_to_rgb(self._placeholder_color)
        else:
            display = ""
            text_color = _color_name_to_rgb(self._text_color)

        max_w = self.image.get_width() - 2 * padding
        if max_w <= 0:
            return

        # Measure the width of text up to the cursor to determine scroll offset.
        cursor_display_pos = self._display_text(self._input_value[: self._cursor_pos])
        cursor_x_full = font.size(cursor_display_pos)[0]

        # Scroll so the cursor is always visible.
        scroll_x = max(0, cursor_x_full - max_w)

        if display:
            text_surf = font.render(display, True, text_color)
            y_pos = (self.image.get_height() - text_surf.get_height()) // 2
            src_x = scroll_x
            src_w = min(text_surf.get_width() - src_x, max_w)
            if src_w > 0:
                src_rect = pygame.Rect(src_x, 0, src_w, text_surf.get_height())
                self.image.blit(text_surf, (padding, y_pos), src_rect)
        else:
            y_pos = (self.image.get_height() - font.get_height()) // 2

        # Draw cursor as a thin vertical line.
        if (
            self._is_focused
            and self._cursor_visible
            and has_value
            or (self._is_focused and self._cursor_visible)
        ):
            cursor_x_screen = padding + (cursor_x_full - scroll_x)
            cursor_x_screen = max(padding, min(cursor_x_screen, padding + max_w))
            cursor_h = font.get_height()
            cy = (self.image.get_height() - cursor_h) // 2
            pygame.draw.line(
                self.image,
                _color_name_to_rgb(self._text_color),
                (cursor_x_screen, cy),
                (cursor_x_screen, cy + cursor_h),
                2,
            )

        # Draw selection highlight (simplified: just behind the rendered text).
        if self._selection_start is not None and has_value:
            disp = self._display_text(self._input_value)
            a = min(self._selection_start, self._selection_end)
            b = max(self._selection_start, self._selection_end)
            x_a = font.size(self._display_text(self._input_value[:a]))[0] - scroll_x
            x_b = font.size(self._display_text(self._input_value[:b]))[0] - scroll_x
            x_a = max(0, x_a)
            x_b = min(max_w, x_b)
            if x_b > x_a:
                sel_surf = pygame.Surface(
                    (x_b - x_a, font.get_height()), pygame.SRCALPHA
                )
                sel_surf.fill((100, 149, 237, 100))  # cornflower blue, semi-transparent
                sy = (self.image.get_height() - font.get_height()) // 2
                self.image.blit(sel_surf, (padding + x_a, sy))
                # Re-blit text on top of the highlight so it's readable.
                if disp:
                    text_surf = font.render(disp, True, text_color)
                    src_x = scroll_x
                    src_w = min(text_surf.get_width() - src_x, max_w)
                    if src_w > 0:
                        src_rect = pygame.Rect(src_x, 0, src_w, text_surf.get_height())
                        self.image.blit(text_surf, (padding, y_pos), src_rect)

    # ── public API ──────────────────────────────────────────────────────────

    @property
    def value(self):
        """The current text value of the input."""
        return self._input_value

    @value.setter
    def value(self, new_value):
        """Set the text value programmatically. Fires when_changed callbacks."""
        self._input_value = str(new_value)
        self._cursor_pos = len(self._input_value)
        self._selection_start = self._selection_end = None
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
        self._input_font = _load_font(self._input_font_path, value)
        self._should_recompute = True

    @property
    def disabled(self):
        """Whether the field is non-interactive (cannot be focused or edited)."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, value):
        self._is_disabled = bool(value)
        if value and self._is_focused:
            _registry.clear_focus()
        self._should_recompute = True

    @property
    def readonly(self):
        """Whether the field can be focused but not edited."""
        return self._readonly

    @readonly.setter
    def readonly(self, value):
        self._readonly = bool(value)
        self._should_recompute = True

    @property
    def password_mode(self):
        """Whether characters are masked with bullets."""
        return self._password_mode

    @password_mode.setter
    def password_mode(self, value):
        self._password_mode = bool(value)
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
        """Create a copy of this text input.

        Value, focus state, and when_changed/when_submit callbacks are not
        copied — register new callbacks on the returned instance."""
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
            font=self._input_font_path,
            border_color=self._border_color,
            border_width=self._border_width,
            border_radius=self._border_radius,
            max_length=self._max_length,
            transparency=self._transparency,
            size=self._size,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
            readonly=self._readonly,
            password_mode=self._password_mode,
        )

    def remove(self):
        _registry.unregister(self)
        if self._is_focused:
            _registry.clear_focus()
        super().remove()
