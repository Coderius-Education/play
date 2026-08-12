"""Tests for widget guards whose only symptom is a silent leak or misfire.

Each guard here is invisible to the rest of the suite: remove it and every
other test still passes, while a password reaches the system clipboard, a
scroll toggles controls, or a hidden widget keeps mutating its value.
"""

import pytest
import pygame
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state, handle_mouse_events
from tests.conftest import click_at


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": ""})


def _fake_scrap(monkeypatch, clipboard=""):
    store = {"text": clipboard}
    monkeypatch.setattr(pygame.scrap, "init", lambda: None)
    monkeypatch.setattr(
        pygame.scrap, "put_text", lambda text: store.__setitem__("text", text)
    )
    monkeypatch.setattr(pygame.scrap, "get_text", lambda: store["text"])
    return store


# ── the mouse wheel is not a click ────────────────────────────────────────────


@pytest.mark.parametrize("wheel_button", [4, 5])
def test_wheel_button_does_not_register_a_click(wheel_button):
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": wheel_button}
    )
    handle_mouse_events(event)
    assert mouse_state.click_happened is False
    assert mouse._is_clicked is False


def test_scrolling_over_a_checkbox_does_not_toggle_it():
    cb = play.new_checkbox(x=0, y=0, size_px=40)
    mouse.x, mouse.y = 0, 0
    for button in (4, 5):
        handle_mouse_events(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": button}
            )
        )
        cb.update()
    assert cb.checked is False


def test_real_click_still_registers():
    # Guard against "fixing" the wheel case by ignoring buttons entirely.
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (400, 300), "button": 1})
    handle_mouse_events(event)
    assert mouse_state.click_happened is True


# ── password fields never reach the clipboard ─────────────────────────────────


def test_password_mode_blocks_copy(monkeypatch):
    store = _fake_scrap(monkeypatch, clipboard="untouched")
    ti = play.new_text_input(value="hunter2", password_mode=True)
    ti._selection_start, ti._selection_end = 0, 7
    ti._handle_keydown(_keydown(pygame.K_c, mod=pygame.KMOD_CTRL))
    assert store["text"] == "untouched"


def test_password_mode_blocks_cut(monkeypatch):
    store = _fake_scrap(monkeypatch, clipboard="untouched")
    ti = play.new_text_input(value="hunter2", password_mode=True)
    ti._selection_start, ti._selection_end = 0, 7
    ti._handle_keydown(_keydown(pygame.K_x, mod=pygame.KMOD_CTRL))
    assert store["text"] == "untouched"
    assert ti.value == "hunter2"  # cut must not delete either


# ── pasted newlines are flattened ─────────────────────────────────────────────


def test_paste_flattens_newlines(monkeypatch):
    _fake_scrap(monkeypatch, clipboard="a\nb\r\nc\rd")
    ti = play.new_text_input(value="")
    ti._handle_keydown(_keydown(pygame.K_v, mod=pygame.KMOD_CTRL))
    assert "\n" not in ti.value
    assert "\r" not in ti.value
    assert ti.value == "a b c d"
    assert ti._cursor_pos == len(ti.value)


# ── decorative widgets must not swallow clicks ────────────────────────────────


def test_progress_bar_does_not_steal_clicks_from_a_button():
    btn = play.new_button("Go", x=0, y=0, width=120, height=40)
    play.new_progress_bar(x=0, y=0, width=120, height=40)
    mouse.x, mouse.y = 0, 0
    mouse._is_clicked = True
    mouse_state.click_happened = True
    mouse_state.resolve_click_owner()
    try:
        assert mouse_state.click_owner is btn
    finally:
        mouse_state.clear()
        mouse._is_clicked = False


def test_tooltip_does_not_steal_clicks_from_its_target():
    btn = play.new_button("Go", x=0, y=0, width=120, height=40)
    # Zero offsets put the bubble directly under the cursor, so this would
    # actually catch a Tooltip that started claiming clicks.
    tip = play.new_tooltip("Click me", target=btn, offset_x=0, offset_y=0)
    mouse.x, mouse.y = 0, 0
    tip.update()  # tooltip is showing, on top at layer 100
    mouse._is_clicked = True
    mouse_state.click_happened = True
    mouse_state.resolve_click_owner()
    try:
        assert mouse_state.click_owner is btn
    finally:
        mouse_state.clear()
        mouse._is_clicked = False


# ── a disabled or hidden slider is inert ──────────────────────────────────────


def _start_drag(slider):
    click_at(0, 0, slider, hold=True)


def test_disabled_slider_ignores_a_drag():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    s.disabled = True
    received = []
    s.when_changed(received.append)
    _start_drag(s)
    mouse.x = -80
    s.update()
    assert s.value == 50
    assert received == []
    mouse._is_clicked = False


def test_hidden_slider_ignores_a_drag():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    s.hide()
    mouse.x = -80
    s.update()
    assert s.value == 50
    mouse._is_clicked = False


def test_disabling_mid_drag_does_not_resume_on_re_enable():
    # Regression: the _dragging reset lived inside the enabled branch, so the
    # flag survived and the drag resumed without a fresh click.
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    s.disabled = True
    s.update()
    assert s._dragging is False
    s.disabled = False
    mouse.x = -80
    s.update()
    assert s.value == 50
    mouse._is_clicked = False


# ── colour setters survive the next frame ─────────────────────────────────────


def test_text_input_color_setter_survives_update():
    ti = play.new_text_input(value="hi", x=0, y=0, color="white")
    ti.color = "pink"
    ti.update()
    assert ti.color == "pink"


def test_dropdown_color_setter_survives_update():
    dd = play.new_dropdown(options=["A", "B"], x=0, y=0, color="white")
    mouse.x, mouse.y = 999, 999  # keep it unhovered
    dd.color = "pink"
    dd.update()
    assert dd.color == "pink"
