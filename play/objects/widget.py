"""Shared behaviour for interactive widgets.

Hover callbacks and the disabled-aware click registration started out on
Button alone. Every other widget inherited neither, so ``disabled`` quietly
meant two different things depending on which widget you used — the widget
ignored the click itself, but the game's own ``when_clicked`` handler still
ran — and only Button could report hover.

Mixing this in ahead of the base class gives every interactive widget the
same contract. Subclasses must:

* list this class *first* in their bases, so ``when_clicked`` here overrides
  ``Sprite``'s,
* call :meth:`_init_widget` from ``__init__`` before ``super().__init__()``,
* call :meth:`_track_hover` once per frame from ``update()``.
"""

import inspect as _inspect

from ..utils import reject_async_callback as _reject_async


class WidgetMixin:
    """Hover callbacks plus click callbacks that respect ``disabled``."""

    # Interactive: a click goes to the top-most widget under the cursor.
    # See MouseState.resolve_click_owner.
    _is_widget = True

    def _init_widget(self):
        """Initialise hover state. Call before ``super().__init__()``."""
        self._hover_callbacks = []
        self._unhover_callbacks = []
        self._was_hovered = False

    # ── hover ─────────────────────────────────────────────────────────────────

    def _end_hover(self):
        """Run when_unhover once for an active hover, then clear the flag."""
        if not self._was_hovered:
            return
        for cb in self._unhover_callbacks:
            cb()
        self._was_hovered = False

    def _track_hover(self, hovered):
        """Fire when_hover / when_unhover on the edges of *hovered*.

        Pass ``False`` while disabled or hidden: that closes out an active
        hover instead of stranding whatever the callback toggled.
        """
        if hovered and not self._was_hovered:
            for cb in self._hover_callbacks:
                cb()
            self._was_hovered = True
        elif not hovered:
            self._end_hover()

    def when_hover(self, func):
        """Decorator — *func()* is called when the pointer enters the widget."""
        _reject_async(func, "when_hover")
        self._hover_callbacks.append(func)
        return func

    def when_unhover(self, func):
        """Decorator — *func()* is called when the pointer leaves the widget."""
        _reject_async(func, "when_unhover")
        self._unhover_callbacks.append(func)
        return func

    # ── clicks that respect `disabled` ────────────────────────────────────────

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
        # Expose the wrapped callback's signature so the dispatcher's arg-count
        # check (callback_helpers._resolve_callback_args) still works — otherwise
        # the *args wrapper reads as zero args and call_with_sprite=True raises.
        try:
            guarded.__signature__ = _inspect.signature(callback)
        except (ValueError, TypeError):
            pass
        return guarded

    def when_clicked(self, callback, call_with_sprite=False):
        """Register a click callback; the callback is silently skipped when disabled."""
        return super().when_clicked(self._guard_disabled(callback), call_with_sprite)

    def when_click_released(self, callback, call_with_sprite=False):
        """Register a click-release callback; skipped when disabled."""
        return super().when_click_released(
            self._guard_disabled(callback), call_with_sprite
        )
