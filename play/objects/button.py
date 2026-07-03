"""This module contains the Button class, a Box with a text label and hover/press/disabled state."""

import inspect as _inspect

from .box import Box
from ..io.mouse import mouse
from ..utils import color_name_to_rgb as _color_name_to_rgb, load_font as _load_font


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
        click_color=None,
        text_color="white",
        font_size=20,
        font=None,
        border_radius=6,
        transparency=100,
        size=100,
        anchor=None,
        layer=10,
        disabled=False,
        disabled_color="gray",
        disabled_text_color=None,
    ):
        self._button_text = text
        self._hover_color = hover_color
        self._base_color = color
        self._click_color = click_color
        self._text_color = text_color
        self._button_font_size = font_size
        self._button_font_path = font
        self._button_font = _load_font(font, font_size)
        self._is_disabled = disabled
        self._disabled_color = disabled_color
        self._disabled_text_color = disabled_text_color
        self._was_hovered = False
        self._hover_callbacks = []
        self._unhover_callbacks = []
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
        """Set hover/press/disabled colour then delegate to Sprite.update() → _render()."""
        if self._is_disabled:
            self._color = self._disabled_color
            self._was_hovered = False
        else:
            hovered = mouse.is_touching(self)
            pressed = hovered and mouse._is_clicked

            if hovered and not self._was_hovered:
                for cb in self._hover_callbacks:
                    cb()
            elif not hovered and self._was_hovered:
                for cb in self._unhover_callbacks:
                    cb()
            self._was_hovered = hovered

            if pressed:
                if self._click_color is not None:
                    self._color = self._click_color
                else:
                    rgba = _color_name_to_rgb(self._hover_color)
                    r, g, b = rgba[0], rgba[1], rgba[2]
                    self._color = (
                        max(0, int(r * 0.75)),
                        max(0, int(g * 0.75)),
                        max(0, int(b * 0.75)),
                    )
            elif hovered:
                self._color = self._hover_color
            else:
                self._color = self._base_color
        super().update()

    def _render(self):
        """Draw box background then blit the text label on top."""
        super()._render()  # Box._render()
        self._blit_text()

    def _blit_text(self):
        if self._is_disabled and self._disabled_text_color is not None:
            color = _color_name_to_rgb(self._disabled_text_color)
        else:
            color = _color_name_to_rgb(self._text_color)
        text_surf = self._button_font.render(self._button_text, True, color)
        text_rect = text_surf.get_rect(
            center=(self.image.get_width() // 2, self.image.get_height() // 2)
        )
        self.image.blit(text_surf, text_rect)

    # ── override when_clicked to honour disabled state ───────────────────────

    def _guard_disabled(self, callback):
        """Wrap *callback* so it's skipped while disabled, preserving async-ness."""
        if _inspect.iscoroutinefunction(callback):

            async def guarded(*args, **kwargs):
                if not self._is_disabled:
                    await callback(*args, **kwargs)

        else:

            def guarded(*args, **kwargs):
                if not self._is_disabled:
                    callback(*args, **kwargs)

        guarded.__name__ = getattr(callback, "__name__", "guarded")
        return guarded

    def when_clicked(self, callback, call_with_sprite=False):
        """Register a click callback; the callback is silently skipped when disabled."""
        return super().when_clicked(self._guard_disabled(callback), call_with_sprite)

    def when_click_released(self, callback, call_with_sprite=False):
        """Register a click-release callback; skipped when disabled."""
        return super().when_click_released(
            self._guard_disabled(callback), call_with_sprite
        )

    # ── hover callbacks ───────────────────────────────────────────────────────

    def when_hover(self, func):
        """Decorator — *func()* is called when the mouse pointer enters the button."""
        if _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} is async. when_hover callbacks must be regular functions."
            )
        self._hover_callbacks.append(func)
        return func

    def when_unhover(self, func):
        """Decorator — *func()* is called when the mouse pointer leaves the button."""
        if _inspect.iscoroutinefunction(func):
            raise TypeError(
                f"{func.__name__} is async. when_unhover callbacks must be regular functions."
            )
        self._unhover_callbacks.append(func)
        return func

    # ── properties ────────────────────────────────────────────────────────────

    @property
    def text(self):
        """The button label."""
        return self._button_text

    @text.setter
    def text(self, value):
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
    def click_color(self):
        """The background colour while the mouse button is held down (None = auto-darken)."""
        return self._click_color

    @click_color.setter
    def click_color(self, value):
        self._click_color = value
        self._should_recompute = True

    @property
    def disabled(self):
        """Whether the button is disabled (non-interactive, visually greyed out)."""
        return self._is_disabled

    @disabled.setter
    def disabled(self, value):
        self._is_disabled = bool(value)
        self._should_recompute = True

    @property
    def disabled_color(self):
        """Background colour shown when the button is disabled."""
        return self._disabled_color

    @disabled_color.setter
    def disabled_color(self, value):
        self._disabled_color = value
        self._should_recompute = True

    @property
    def font_size(self):
        """The font size of the button label."""
        return self._button_font_size

    @font_size.setter
    def font_size(self, value):
        self._button_font_size = value
        self._button_font = _load_font(self._button_font_path, value)
        self._should_recompute = True

    def clone(self):
        """Create a copy of this button."""
        return Button(
            text=self._button_text,
            x=self._anchor_ox if self._anchor else self.x,
            y=self._anchor_oy if self._anchor else self.y,
            width=self._width,
            height=self._height,
            color=self._base_color,
            hover_color=self._hover_color,
            click_color=self._click_color,
            text_color=self._text_color,
            font_size=self._button_font_size,
            font=self._button_font_path,
            border_radius=self._border_radius,
            transparency=self._transparency,
            size=self._size,
            anchor=self._anchor,
            layer=self._layer,
            disabled=self._is_disabled,
            disabled_color=self._disabled_color,
            disabled_text_color=self._disabled_text_color,
        )
