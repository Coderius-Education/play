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


def test_tab_with_all_fields_disabled_clears_focus():
    # Regression: focus_next() must not strand focus when nothing is focusable.
    ti1 = play.new_text_input(x=-100, y=0)
    ti2 = play.new_text_input(x=100, y=0)
    registry.focus(ti1)
    # Disable every field via the private attr (bypasses the disabled setter).
    ti1._is_disabled = True
    ti2._is_disabled = True
    ti1._handle_keydown(_keydown(pygame.K_TAB))
    assert globals_list.focused_text_input is None
    assert ti1._is_focused is False


def test_copy_survives_unavailable_scrap(monkeypatch):
    # Regression: Ctrl+C/Ctrl+X must not propagate when pygame.scrap is unavailable.
    ti = play.new_text_input(value="hello")
    registry.focus(ti)
    ti._selection_start, ti._selection_end = 0, 5

    def _boom(*_args, **_kwargs):
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", _boom)
    # Should not raise.
    ti._handle_keydown(_keydown(pygame.K_c, mod=pygame.KMOD_CTRL))


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


# ── clipboard (mocked pygame.scrap) ──────────────────────────────────────────


def _fake_scrap(monkeypatch, clipboard=""):
    """Replace pygame.scrap with an in-memory fake; returns the storage dict."""
    store = {"text": clipboard}
    monkeypatch.setattr(pygame.scrap, "init", lambda: None)
    monkeypatch.setattr(
        pygame.scrap, "put_text", lambda text: store.__setitem__("text", text)
    )
    monkeypatch.setattr(pygame.scrap, "get_text", lambda: store["text"])
    return store


def test_ctrl_c_copies_selection(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    store = _fake_scrap(monkeypatch)
    ti = play.new_text_input(value="hello")
    ti._selection_start, ti._selection_end = 1, 4
    ti._handle_keydown(_keydown(pygame.K_c, mod=pygame.KMOD_CTRL))
    assert store["text"] == "ell"
    assert ti.value == "hello"  # copy does not modify the value


def test_ctrl_c_without_selection_copies_nothing(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    store = _fake_scrap(monkeypatch, clipboard="untouched")
    ti = play.new_text_input(value="hello")
    ti._handle_keydown(_keydown(pygame.K_c, mod=pygame.KMOD_CTRL))
    assert store["text"] == "untouched"


def test_ctrl_x_cuts_selection(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    store = _fake_scrap(monkeypatch)
    ti = play.new_text_input(value="hello")
    changed = []
    ti.when_changed(changed.append)
    ti._selection_start, ti._selection_end = 1, 4
    ti._handle_keydown(_keydown(pygame.K_x, mod=pygame.KMOD_CTRL))
    assert store["text"] == "ell"
    assert ti.value == "ho"
    assert changed == ["ho"]


def test_ctrl_v_pastes_at_cursor(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    _fake_scrap(monkeypatch, clipboard="XY")
    ti = play.new_text_input(value="ab")
    changed = []
    ti.when_changed(changed.append)
    ti._cursor_pos = 1
    ti._handle_keydown(_keydown(pygame.K_v, mod=pygame.KMOD_CTRL))
    assert ti.value == "aXYb"
    assert ti._cursor_pos == 3
    assert changed == ["aXYb"]


def test_ctrl_v_replaces_selection(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    _fake_scrap(monkeypatch, clipboard="i")
    ti = play.new_text_input(value="hello")
    ti._selection_start, ti._selection_end = 1, 4
    ti._handle_keydown(_keydown(pygame.K_v, mod=pygame.KMOD_CTRL))
    assert ti.value == "hio"


def test_ctrl_v_respects_max_length(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)
    _fake_scrap(monkeypatch, clipboard="cdef")
    ti = play.new_text_input(value="ab", max_length=4)
    ti._handle_keydown(_keydown(pygame.K_v, mod=pygame.KMOD_CTRL))
    assert ti.value == "abcd"


def test_paste_survives_unavailable_scrap(monkeypatch):
    monkeypatch.setattr(pygame.key, "get_mods", lambda: pygame.KMOD_CTRL)

    def _boom():
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", _boom)
    ti = play.new_text_input(value="safe")
    ti._handle_keydown(_keydown(pygame.K_v, mod=pygame.KMOD_CTRL))
    assert ti.value == "safe"


# ── remaining editing / rendering paths ──────────────────────────────────────


def test_delete_key_removes_selection():
    ti = play.new_text_input(value="hello")
    ti._selection_start, ti._selection_end = 1, 4
    ti._handle_keydown(_keydown(pygame.K_DELETE))
    assert ti.value == "ho"
    assert ti._selection_start is None


def test_cursor_blink_toggles_after_interval():
    ti = play.new_text_input()
    registry.focus(ti)
    ti._cursor_visible = True
    ti._last_blink = pygame.time.get_ticks() - 600  # past the 500ms interval
    ti.update()
    assert ti._cursor_visible is False


def test_selection_highlight_is_rendered():
    ti = play.new_text_input(value="hello", width=200, height=40)
    registry.focus(ti)
    ti._cursor_visible = False
    ti._last_blink = pygame.time.get_ticks()
    ti._should_recompute = True
    ti.update()
    before = pygame.image.tobytes(ti.image, "RGBA")
    ti._selection_start, ti._selection_end = 0, 5
    ti._last_blink = pygame.time.get_ticks()
    ti._should_recompute = True
    ti.update()
    after = pygame.image.tobytes(ti.image, "RGBA")
    assert before != after  # the highlight visibly changes the rendered image


# ── property setters ─────────────────────────────────────────────────────────


def test_placeholder_setter():
    ti = play.new_text_input(placeholder="old")
    ti.placeholder = "new"
    assert ti.placeholder == "new"
    assert ti._should_recompute is True


def test_text_color_setter():
    ti = play.new_text_input()
    ti.text_color = "red"
    assert ti.text_color == "red"


def test_placeholder_color_setter():
    ti = play.new_text_input()
    ti.placeholder_color = "purple"
    assert ti.placeholder_color == "purple"


def test_font_size_setter_reloads_font():
    ti = play.new_text_input()
    ti.font_size = 30
    assert ti.font_size == 30
    assert ti._input_font.get_height() > 0


def test_readonly_setter():
    ti = play.new_text_input()
    ti.readonly = True
    assert ti.readonly is True
    ti._handle_text_input("x")
    assert ti.value == ""  # readonly blocks typing


def test_unregister_twice_is_harmless():
    ti = play.new_text_input()
    registry.unregister(ti)
    registry.unregister(ti)  # second call must not raise


def test_tab_from_stale_focus_goes_to_first_field():
    a = play.new_text_input()
    b = play.new_text_input()
    registry.focus(b)
    b.disabled = True  # focused widget drops out of the Tab order
    registry.focus_next()
    assert globals_list.focused_text_input is a


def test_readonly_blocks_editing_keys():
    ti = play.new_text_input(value="abc", readonly=True)
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "abc"  # the readonly guard stops editing keys


def test_disabling_focused_field_clears_focus():
    ti = play.new_text_input()
    registry.focus(ti)
    ti.disabled = True
    assert globals_list.focused_text_input is None
