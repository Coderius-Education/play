"""Tests for behaviour shared by every interactive widget.

Hover callbacks and the disabled click-guard used to exist on Button alone,
so `disabled` meant two different things depending on the widget: the widget
ignored the click itself, but the game's own when_clicked handler still ran.
"""

import pytest
import play
from play.io.mouse import mouse
from play.objects.widget import WidgetMixin


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _make(kind):
    """One interactive widget of each kind, centred and 100x50-ish."""
    if kind == "button":
        return play.new_button("Go", x=0, y=0, width=100, height=50)
    if kind == "checkbox":
        return play.new_checkbox(x=0, y=0, size_px=40)
    if kind == "slider":
        return play.new_slider(min_value=0, max_value=100, x=0, y=0, width=100)
    if kind == "dropdown":
        return play.new_dropdown(options=["A", "B"], x=0, y=0, width=100, height=40)
    if kind == "text_input":
        return play.new_text_input(x=0, y=0, width=100, height=40)
    if kind == "radio_button":
        return play.new_radio_button(
            "A", value="a", group=play.new_radio_group(), x=0, y=0
        )
    raise AssertionError(kind)


KINDS = ["button", "checkbox", "slider", "dropdown", "text_input", "radio_button"]


def _settle_outside(widget):
    """Move off the widget and update, so hover starts from a known False."""
    mouse.x, mouse.y = 999, 999
    widget.update()


# ── every interactive widget reports hover ────────────────────────────────────


@pytest.mark.parametrize("kind", KINDS)
def test_every_widget_supports_hover_callbacks(kind):
    widget = _make(kind)
    _settle_outside(widget)
    events = []
    widget.when_hover(lambda: events.append("hover"))
    widget.when_unhover(lambda: events.append("unhover"))

    mouse.x, mouse.y = 0, 0
    widget.update()
    assert events == ["hover"]

    widget.update()  # still hovering — must not fire again
    assert events == ["hover"]

    mouse.x, mouse.y = 999, 999
    widget.update()
    assert events == ["hover", "unhover"]


@pytest.mark.parametrize("kind", KINDS)
def test_disabling_while_hovered_closes_the_hover(kind):
    widget = _make(kind)
    _settle_outside(widget)
    events = []
    widget.when_unhover(lambda: events.append("unhover"))
    mouse.x, mouse.y = 0, 0
    widget.update()
    widget.disabled = True
    widget.update()
    assert events == ["unhover"]


@pytest.mark.parametrize("kind", KINDS)
def test_hover_callbacks_reject_async(kind):
    widget = _make(kind)
    with pytest.raises(TypeError):

        @widget.when_hover
        async def _handler():
            pass


# ── `disabled` also suppresses the game's own click handler ───────────────────


@pytest.mark.parametrize("kind", KINDS)
def test_when_clicked_is_disabled_aware_on_every_widget(kind):
    # The dispatcher fires callbacks as asyncio tasks, so asserting through
    # handle_sprite_click() in a sync test would exercise nothing. Check that
    # the guard is installed, and test the wrapper it installs directly below.
    widget = _make(kind)
    assert type(widget).when_clicked is WidgetMixin.when_clicked
    assert type(widget).when_click_released is WidgetMixin.when_click_released


@pytest.mark.parametrize("kind", KINDS)
def test_click_callback_is_suppressed_only_while_disabled(kind):
    widget = _make(kind)
    fired = []
    guarded = widget._guard_disabled(lambda: fired.append(1))

    widget.disabled = True
    guarded()
    assert fired == []  # disabled: the game's own handler is skipped

    widget.disabled = False
    guarded()
    assert fired == [1]  # enabled: it runs normally


# ── decorative widgets stay out of it ─────────────────────────────────────────


def test_progress_bar_and_tooltip_are_not_widgets():
    bar = play.new_progress_bar(x=0, y=0)
    tip = play.new_tooltip("hi", target=bar)
    assert bar._is_widget is False
    assert tip._is_widget is False
    assert not hasattr(bar, "_hover_callbacks")
