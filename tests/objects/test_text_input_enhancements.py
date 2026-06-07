"""Tests for enhanced TextInput features: cursor movement, clipboard, disabled, password, tab."""

import pygame
import pytest
import play
from play.globals import globals_list
from play.objects import text_input_registry as registry


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": ""})


# ── cursor position ───────────────────────────────────────────────────────────


def test_cursor_at_end_after_creation():
    ti = play.new_text_input(value="abc")
    assert ti._cursor_pos == 3


def test_left_arrow_moves_cursor():
    ti = play.new_text_input(value="abc")
    ti._handle_keydown(_keydown(pygame.K_LEFT))
    assert ti._cursor_pos == 2


def test_right_arrow_moves_cursor():
    ti = play.new_text_input(value="abc")
    ti._cursor_pos = 0
    ti._handle_keydown(_keydown(pygame.K_RIGHT))
    assert ti._cursor_pos == 1


def test_left_arrow_at_start_is_noop():
    ti = play.new_text_input(value="abc")
    ti._cursor_pos = 0
    ti._handle_keydown(_keydown(pygame.K_LEFT))
    assert ti._cursor_pos == 0


def test_right_arrow_at_end_is_noop():
    ti = play.new_text_input(value="abc")
    ti._handle_keydown(_keydown(pygame.K_RIGHT))
    assert ti._cursor_pos == 3  # unchanged


def test_home_moves_cursor_to_start():
    ti = play.new_text_input(value="abc")
    ti._handle_keydown(_keydown(pygame.K_HOME))
    assert ti._cursor_pos == 0


def test_end_moves_cursor_to_end():
    ti = play.new_text_input(value="abc")
    ti._cursor_pos = 0
    ti._handle_keydown(_keydown(pygame.K_END))
    assert ti._cursor_pos == 3


def test_insert_at_cursor_position():
    ti = play.new_text_input(value="ac")
    ti._cursor_pos = 1
    ti._handle_text_input("b")
    assert ti.value == "abc"
    assert ti._cursor_pos == 2


def test_backspace_deletes_before_cursor():
    ti = play.new_text_input(value="abc")
    ti._cursor_pos = 2  # cursor between b and c
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "ac"
    assert ti._cursor_pos == 1


def test_delete_removes_char_after_cursor():
    ti = play.new_text_input(value="abc")
    ti._cursor_pos = 1
    ti._handle_keydown(_keydown(pygame.K_DELETE))
    assert ti.value == "ac"
    assert ti._cursor_pos == 1


# ── selection ─────────────────────────────────────────────────────────────────


def test_ctrl_a_selects_all(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    ti = play.new_text_input(value="hello")
    ti._handle_keydown(_keydown(pygame.K_a, mod=pygame.KMOD_CTRL))
    assert ti._selection_start == 0
    assert ti._selection_end == 5


def test_backspace_on_selection_deletes_selection():
    ti = play.new_text_input(value="hello")
    ti._selection_start = 1
    ti._selection_end = 4  # selects "ell"
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "ho"
    assert ti._selection_start is None


# ── disabled mode ─────────────────────────────────────────────────────────────


def test_disabled_prevents_focus():
    from play.io.mouse import mouse
    from play.core.mouse_loop import mouse_state
    ti = play.new_text_input(x=0, y=0, width=200, height=40, disabled=True)
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    ti.update()
    assert not ti._is_focused


def test_disabled_prevents_text_input():
    ti = play.new_text_input(value="hello", disabled=True)
    ti._handle_text_input("!")
    assert ti.value == "hello"


def test_disabled_setter():
    ti = play.new_text_input()
    ti.disabled = True
    assert ti.disabled is True


def test_disabled_default_false():
    ti = play.new_text_input()
    assert ti.disabled is False


# ── readonly mode ─────────────────────────────────────────────────────────────


def test_readonly_prevents_text_input():
    ti = play.new_text_input(value="hello", readonly=True)
    ti._handle_text_input("!")
    assert ti.value == "hello"


def test_readonly_allows_navigation():
    ti = play.new_text_input(value="abc", readonly=True)
    ti._cursor_pos = 3
    ti._handle_keydown(_keydown(pygame.K_LEFT))
    assert ti._cursor_pos == 2


def test_readonly_setter():
    ti = play.new_text_input()
    ti.readonly = True
    assert ti.readonly is True


# ── password mode ─────────────────────────────────────────────────────────────


def test_password_mode_masks_display():
    ti = play.new_text_input(value="secret", password_mode=True)
    display = ti._display_text(ti.value)
    assert display == "••••••"
    assert "s" not in display


def test_password_mode_does_not_change_value():
    ti = play.new_text_input(value="secret", password_mode=True)
    assert ti.value == "secret"


def test_password_mode_setter():
    ti = play.new_text_input()
    ti.password_mode = True
    assert ti.password_mode is True


def test_password_mode_default_false():
    ti = play.new_text_input()
    assert ti.password_mode is False


# ── Tab navigation ────────────────────────────────────────────────────────────


def test_tab_key_moves_to_next_input():
    ti1 = play.new_text_input(x=-100, y=0)
    ti2 = play.new_text_input(x=100, y=0)
    registry.focus(ti1)
    ti1._handle_keydown(_keydown(pygame.K_TAB))
    assert globals_list.focused_text_input is ti2


def test_tab_order_wraps_around():
    ti1 = play.new_text_input(x=-100, y=0)
    ti2 = play.new_text_input(x=100, y=0)
    registry.focus(ti2)
    ti2._handle_keydown(_keydown(pygame.K_TAB))
    assert globals_list.focused_text_input is ti1


def test_tab_skips_disabled():
    ti1 = play.new_text_input(x=-100, y=0)
    ti2 = play.new_text_input(x=0, y=0, disabled=True)
    ti3 = play.new_text_input(x=100, y=0)
    registry.focus(ti1)
    ti1._handle_keydown(_keydown(pygame.K_TAB))
    # ti2 is disabled, so focus should go to ti3
    assert globals_list.focused_text_input is ti3


def test_register_on_creation():
    from play.objects.text_input_registry import _tab_order
    ti = play.new_text_input()
    assert ti in _tab_order


def test_unregister_on_remove():
    from play.objects.text_input_registry import _tab_order
    ti = play.new_text_input()
    ti.remove()
    assert ti not in _tab_order


# ── clone preserves new fields ────────────────────────────────────────────────


def test_clone_preserves_disabled():
    ti = play.new_text_input(disabled=True)
    c = ti.clone()
    assert c.disabled is True


def test_clone_preserves_readonly():
    ti = play.new_text_input(readonly=True)
    c = ti.clone()
    assert c.readonly is True


def test_clone_preserves_password_mode():
    ti = play.new_text_input(password_mode=True)
    c = ti.clone()
    assert c.password_mode is True
