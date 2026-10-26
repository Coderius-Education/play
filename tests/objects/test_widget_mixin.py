"""Tests for behaviour shared by every interactive widget.

Hover callbacks and the disabled click-guard used to exist on Button alone,
so `disabled` meant two different things depending on the widget: the widget
ignored the click itself, but the game's own when_clicked handler still ran.
"""

import pytest
import play
from play.io.mouse import mouse
from tests.events.frames import mouse_down, mouse_move, mouse_up, play_frames


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

    widget.update()
    assert events == []

    mouse.x, mouse.y = 0, 0
    widget.update()
    assert events == ["hover"]

    widget.update()  # still hovering — must not fire again
    assert events == ["hover"]

    mouse.x, mouse.y = 999, 999
    widget.update()
    widget.update()
    assert events == ["hover", "unhover"]

    mouse.x, mouse.y = 0, 0
    widget.update()
    assert events == ["hover", "unhover", "hover"]


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


@pytest.mark.parametrize("decorator", ["when_hover", "when_unhover"])
@pytest.mark.parametrize("kind", KINDS)
def test_hover_callbacks_reject_async(kind, decorator):
    widget = _make(kind)

    async def handler():
        pass

    with pytest.raises(TypeError):
        getattr(widget, decorator)(handler)


# ── `disabled` also suppresses the game's own click handler ───────────────────


def _handlers(ran, label):
    """A sync and an async handler that each note *label* in *ran*."""

    def sync_handler():
        ran.append(label)

    async def async_handler():
        ran.append("async " + label)

    return sync_handler, async_handler


@pytest.mark.parametrize("disabled", [False, True])
@pytest.mark.parametrize("kind", KINDS)
def test_the_games_click_handlers_run_only_while_the_widget_is_enabled(kind, disabled):
    widget = _make(kind)
    widget.disabled = disabled
    ran = []
    for handler in _handlers(ran, "clicked"):
        widget.when_clicked(handler)
    for handler in _handlers(ran, "released"):
        widget.when_click_released(handler)

    play_frames([mouse_move(0, 0)], [mouse_down(0, 0)], [mouse_up(0, 0)])

    expected = ["async clicked", "async released", "clicked", "released"]
    assert sorted(ran) == ([] if disabled else expected)
