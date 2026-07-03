"""Tests for enhanced Button features: click_color, disabled, hover callbacks."""

import asyncio
import inspect

import pytest
import play
from play.io.mouse import mouse


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# ── async click callbacks ─────────────────────────────────────────────────────


def test_when_clicked_preserves_async_callback():
    # Regression: the disabled-guard wrapper must stay a coroutine function for
    # async callbacks, otherwise the game loop never awaits them.
    btn = play.new_button()

    async def cb():
        pass

    guarded = btn._guard_disabled(cb)
    assert inspect.iscoroutinefunction(guarded)


def test_when_clicked_sync_callback_stays_sync():
    btn = play.new_button()

    def cb():
        pass

    guarded = btn._guard_disabled(cb)
    assert not inspect.iscoroutinefunction(guarded)


def test_async_guard_runs_when_enabled():
    btn = play.new_button()
    seen = []

    async def cb():
        seen.append(1)

    asyncio.run(btn._guard_disabled(cb)())
    assert seen == [1]


def test_async_guard_skips_when_disabled():
    btn = play.new_button(disabled=True)
    seen = []

    async def cb():
        seen.append(1)

    asyncio.run(btn._guard_disabled(cb)())
    assert seen == []


# ── click_color ───────────────────────────────────────────────────────────────


def test_click_color_stored():
    btn = play.new_button(click_color="navy")
    assert btn._click_color == "navy"


def test_click_color_shown_when_mouse_held():
    btn = play.new_button(x=0, y=0, width=100, height=50, click_color="navy")
    mouse.x = 0
    mouse.y = 0
    mouse._is_clicked = True
    btn.update()
    assert btn._color == "navy"
    mouse._is_clicked = False


def test_auto_darken_when_no_click_color():
    btn = play.new_button(x=0, y=0, width=100, height=50, hover_color="steelblue")
    mouse.x = 0
    mouse.y = 0
    mouse._is_clicked = True
    btn.update()
    # Auto-darken should produce an RGB tuple (darker than the hover colour)
    assert isinstance(btn._color, tuple)
    assert len(btn._color) == 3
    mouse._is_clicked = False


def test_hover_color_when_not_pressed():
    btn = play.new_button(x=0, y=0, width=100, height=50, hover_color="steelblue")
    mouse.x = 0
    mouse.y = 0
    mouse._is_clicked = False
    btn.update()
    assert btn._color == "steelblue"


# ── disabled state ────────────────────────────────────────────────────────────


def test_disabled_defaults_to_false():
    btn = play.new_button()
    assert btn.disabled is False


def test_disabled_setter():
    btn = play.new_button()
    btn.disabled = True
    assert btn.disabled is True


def test_disabled_uses_disabled_color():
    btn = play.new_button(x=0, y=0, width=100, height=50, disabled_color="gray")
    btn.disabled = True
    mouse.x = 0
    mouse.y = 0
    btn.update()
    assert btn._color == "gray"


def test_disabled_ignores_hover():
    btn = play.new_button(
        x=0, y=0, width=100, height=50, hover_color="steelblue", disabled_color="gray"
    )
    btn.disabled = True
    mouse.x = 0
    mouse.y = 0
    btn.update()
    assert btn._color == "gray"  # Not hover_color


def test_disabled_custom_color_stored():
    btn = play.new_button(disabled_color="silver", disabled_text_color="dimgray")
    assert btn._disabled_color == "silver"
    assert btn._disabled_text_color == "dimgray"


def test_disabled_click_callback_suppressed():
    # The guard wrapper must swallow the callback while disabled.
    btn = play.new_button(x=0, y=0, width=100, height=50, disabled=True)
    fired = []
    guarded = btn._guard_disabled(lambda: fired.append(1))
    guarded()
    assert fired == []


def test_enabled_click_callback_fires():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    fired = []
    guarded = btn._guard_disabled(lambda: fired.append(1))
    guarded()
    assert fired == [1]


# ── when_hover / when_unhover callbacks ───────────────────────────────────────


def test_when_hover_fires_on_enter():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    events = []

    @btn.when_hover
    def on_hover():
        events.append("hover")

    mouse.x = 999
    mouse.y = 999
    btn.update()  # outside → no hover

    mouse.x = 0
    mouse.y = 0
    btn.update()  # enters hover area
    assert "hover" in events


def test_when_unhover_fires_on_leave():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    events = []

    @btn.when_unhover
    def on_leave():
        events.append("unhover")

    # Enter hover first
    mouse.x = 0
    mouse.y = 0
    btn.update()
    # Now leave
    mouse.x = 999
    mouse.y = 999
    btn.update()
    assert "unhover" in events


def test_when_hover_not_fired_twice_without_leave():
    btn = play.new_button(x=0, y=0, width=100, height=50)
    count = [0]

    @btn.when_hover
    def on_hover():
        count[0] += 1

    # First ensure mouse is outside so _was_hovered starts False
    mouse.x = 999
    mouse.y = 999
    btn.update()
    # Now move into hover area
    mouse.x = 0
    mouse.y = 0
    btn.update()  # enters hover — should fire
    btn.update()  # still hovering — should NOT fire again
    assert count[0] == 1  # fired exactly once


def test_when_hover_rejects_async():
    btn = play.new_button()
    with pytest.raises(TypeError):

        @btn.when_hover
        async def bad():
            pass


def test_when_unhover_rejects_async():
    btn = play.new_button()
    with pytest.raises(TypeError):

        @btn.when_unhover
        async def bad():
            pass


# ── clone includes new fields ─────────────────────────────────────────────────


def test_clone_preserves_disabled():
    btn = play.new_button(disabled=True, disabled_color="silver")
    c = btn.clone()
    assert c._is_disabled is True
    assert c._disabled_color == "silver"


def test_clone_preserves_click_color():
    btn = play.new_button(click_color="darkblue")
    c = btn.clone()
    assert c._click_color == "darkblue"
