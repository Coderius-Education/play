"""Tests for enhanced TextInput features: cursor movement, clipboard, disabled, password, tab."""

import pygame
import pytest
import play
from play.globals import globals_list
from play.objects.widgets import text_input_registry as registry
from play.utils import color_name_to_rgb
from tests.conftest import click_at, count_color

CTRL = pygame.KMOD_CTRL


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": ""})


def _press(field, *keys, mod=0):
    for key in keys:
        field._handle_keydown(_keydown(key, mod))


def _image(sprite):
    return pygame.image.tobytes(sprite.image, "RGBA")


# ── cursor position ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "keys, expected",
    [
        ((), "abcX"),
        ((pygame.K_LEFT,), "abXc"),
        ((pygame.K_LEFT, pygame.K_LEFT, pygame.K_RIGHT), "abXc"),
        ((pygame.K_RIGHT,), "abcX"),
        ((pygame.K_HOME,), "Xabc"),
        ((pygame.K_HOME, pygame.K_LEFT), "Xabc"),
        ((pygame.K_HOME, pygame.K_RIGHT), "aXbc"),
        ((pygame.K_HOME, pygame.K_END), "abcX"),
    ],
    ids=[
        "starts_at_end",
        "left",
        "right",
        "right_at_end",
        "home",
        "left_at_start",
        "right_from_start",
        "end",
    ],
)
def test_typing_lands_where_the_arrow_keys_put_the_cursor(keys, expected):
    ti = play.new_text_input(value="abc")
    _press(ti, *keys)
    ti._handle_text_input("X")
    assert ti.value == expected


def test_backspace_deletes_before_cursor():
    ti = play.new_text_input(value="abc")
    _press(ti, pygame.K_LEFT, pygame.K_BACKSPACE)
    assert ti.value == "ac"
    ti._handle_text_input("X")
    assert ti.value == "aXc"


def test_delete_removes_char_after_cursor():
    ti = play.new_text_input(value="abc")
    _press(ti, pygame.K_HOME, pygame.K_RIGHT, pygame.K_DELETE)
    assert ti.value == "ac"
    ti._handle_text_input("X")
    assert ti.value == "aXc"


def test_delete_at_the_end_is_a_no_op():
    ti = play.new_text_input(value="abc")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_DELETE)
    assert ti.value == "abc"
    assert changed == []


@pytest.mark.parametrize("key", [pygame.K_BACKSPACE, pygame.K_DELETE])
def test_deleting_a_character_reports_the_change(key):
    ti = play.new_text_input(value="abc")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_LEFT, key)
    assert changed == [ti.value]


# ── selection ─────────────────────────────────────────────────────────────────


def test_typing_after_ctrl_a_replaces_everything():
    ti = play.new_text_input(value="hello")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_a, mod=CTRL)
    ti._handle_text_input("X")
    assert ti.value == "X"
    assert changed == ["X"]


@pytest.mark.parametrize("key", [pygame.K_BACKSPACE, pygame.K_DELETE])
def test_deleting_after_ctrl_a_empties_the_field_and_reports_it(key):
    ti = play.new_text_input(value="hello")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_a, mod=CTRL)
    _press(ti, key)
    assert ti.value == ""
    assert changed == [""]


def test_an_arrow_key_drops_the_selection():
    ti = play.new_text_input(value="hello")
    _press(ti, pygame.K_a, mod=CTRL)
    _press(ti, pygame.K_LEFT, pygame.K_BACKSPACE)
    assert ti.value == "helo"


def test_ctrl_a_without_ctrl_is_just_the_letter_key():
    ti = play.new_text_input(value="hello")
    _press(ti, pygame.K_a)
    ti._handle_text_input("X")
    assert ti.value == "helloX"


# ── disabled mode ─────────────────────────────────────────────────────────────


def test_disabled_prevents_focus():
    ti = play.new_text_input(x=0, y=0, width=200, height=40, disabled=True)
    click_at(0, 0, ti)
    assert globals_list.focused_text_input is None


def test_disabled_prevents_text_input():
    ti = play.new_text_input(value="hello", disabled=True)
    ti._handle_text_input("!")
    assert ti.value == "hello"


# ── readonly mode ─────────────────────────────────────────────────────────────


def test_readonly_prevents_text_input():
    ti = play.new_text_input(value="hello", readonly=True)
    ti._handle_text_input("!")
    assert ti.value == "hello"


def test_readonly_allows_navigation():
    ti = play.new_text_input(value="abc", readonly=True)
    _press(ti, pygame.K_LEFT)
    ti.readonly = False
    ti._handle_text_input("X")
    assert ti.value == "abXc"


def test_the_readonly_setter_blocks_and_unblocks_editing():
    ti = play.new_text_input(value="abc")
    ti.readonly = True
    assert ti.readonly is True
    ti._handle_text_input("x")
    _press(ti, pygame.K_BACKSPACE)
    assert ti.value == "abc"
    ti.readonly = False
    ti._handle_text_input("x")
    assert ti.value == "abcx"


def test_readonly_blocks_editing_keys():
    ti = play.new_text_input(value="abc", readonly=True)
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "abc"  # the readonly guard stops editing keys


# ── password mode ─────────────────────────────────────────────────────────────


def test_a_password_field_draws_bullets_but_keeps_the_real_value():
    secret = play.new_text_input(value="secret", password_mode=True, x=0, y=100)
    bullets = play.new_text_input(value="••••••", x=0, y=-100)
    assert secret.value == "secret"
    assert _image(secret) == _image(bullets)


def test_turning_password_mode_on_masks_what_is_drawn():
    ti = play.new_text_input(value="secret", x=0, y=100)
    bullets = play.new_text_input(value="••••••", x=0, y=-100)
    assert _image(ti) != _image(bullets)
    ti.password_mode = True
    assert ti.password_mode is True
    ti.update()
    assert _image(ti) == _image(bullets)


# ── Tab navigation ────────────────────────────────────────────────────────────


def test_tab_key_moves_to_next_input():
    ti1 = play.new_text_input(x=-100, y=0)
    ti2 = play.new_text_input(x=100, y=0)
    registry.focus(ti1)
    ti1._handle_keydown(_keydown(pygame.K_TAB))
    assert globals_list.focused_text_input is ti2


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


def test_tab_from_a_field_that_dropped_out_of_the_order_goes_to_the_first_field():
    a = play.new_text_input()
    play.new_text_input()
    c = play.new_text_input()
    registry.focus(c)
    c._is_disabled = True
    registry.focus_next()
    assert globals_list.focused_text_input is a


def test_tab_from_stale_focus_goes_to_first_field():
    a = play.new_text_input()
    b = play.new_text_input()
    registry.focus(b)
    b.disabled = True  # focused widget drops out of the Tab order
    registry.focus_next()
    assert globals_list.focused_text_input is a


def test_removing_a_field_twice_leaves_the_other_fields_in_the_tab_order():
    first = play.new_text_input()
    gone = play.new_text_input()
    last = play.new_text_input()
    gone.remove()
    gone.remove()
    registry.focus(first)
    registry.focus_next()
    assert globals_list.focused_text_input is last


def test_disabling_focused_field_clears_focus():
    ti = play.new_text_input()
    registry.focus(ti)
    ti.disabled = True
    assert globals_list.focused_text_input is None


# ── clone ─────────────────────────────────────────────────────────────────────


def test_a_cloned_field_keeps_its_settings_but_not_its_value():
    ti = play.new_text_input(
        value="secret",
        placeholder="name",
        max_length=3,
        disabled=True,
        readonly=True,
        password_mode=True,
        color="yellow",
        text_color="red",
    )
    c = ti.clone()
    assert c.value == ""
    assert (c.disabled, c.readonly, c.password_mode) == (True, True, True)
    assert c.placeholder == "name"
    c.disabled = c.readonly = False
    c._handle_text_input("abcdef")
    assert c.value == "abc"


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
    store = _fake_scrap(monkeypatch)
    ti = play.new_text_input(value="hello")
    _press(ti, pygame.K_a, pygame.K_c, mod=CTRL)
    assert store["text"] == "hello"
    assert ti.value == "hello"  # copy does not modify the value


def test_ctrl_c_without_selection_copies_nothing(monkeypatch):
    store = _fake_scrap(monkeypatch, clipboard="untouched")
    ti = play.new_text_input(value="hello")
    _press(ti, pygame.K_c, mod=CTRL)
    assert store["text"] == "untouched"


def test_ctrl_x_cuts_selection(monkeypatch):
    store = _fake_scrap(monkeypatch)
    ti = play.new_text_input(value="hello")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_a, pygame.K_x, mod=CTRL)
    assert store["text"] == "hello"
    assert ti.value == ""
    assert changed == [""]


def test_ctrl_v_pastes_at_cursor(monkeypatch):
    _fake_scrap(monkeypatch, clipboard="XY")
    ti = play.new_text_input(value="ab")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_LEFT)
    _press(ti, pygame.K_v, mod=CTRL)
    assert ti.value == "aXYb"
    assert changed == ["aXYb"]
    ti._handle_text_input("!")
    assert ti.value == "aXY!b"


def test_ctrl_v_replaces_selection(monkeypatch):
    _fake_scrap(monkeypatch, clipboard="hi")
    ti = play.new_text_input(value="hello")
    _press(ti, pygame.K_a, pygame.K_v, mod=CTRL)
    assert ti.value == "hi"


def test_ctrl_v_respects_max_length(monkeypatch):
    _fake_scrap(monkeypatch, clipboard="cdef")
    ti = play.new_text_input(value="ab", max_length=4)
    _press(ti, pygame.K_v, mod=CTRL)
    assert ti.value == "abcd"


def test_pasting_an_empty_clipboard_changes_nothing(monkeypatch):
    _fake_scrap(monkeypatch, clipboard="")
    ti = play.new_text_input(value="ab")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_v, mod=CTRL)
    assert ti.value == "ab"
    assert changed == []


def test_paste_survives_unavailable_scrap(monkeypatch):
    def _boom():
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", _boom)
    ti = play.new_text_input(value="safe")
    _press(ti, pygame.K_v, mod=CTRL)
    assert ti.value == "safe"


def test_copy_survives_unavailable_scrap(monkeypatch):
    # Regression: Ctrl+C/Ctrl+X must not propagate when pygame.scrap is unavailable.
    ti = play.new_text_input(value="hello")
    registry.focus(ti)

    def _boom(*_args, **_kwargs):
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", _boom)
    _press(ti, pygame.K_a, pygame.K_c, mod=CTRL)
    assert ti.value == "hello"
    ti._handle_text_input("X")
    assert ti.value == "X"


# ── rendering ────────────────────────────────────────────────────────────────


def test_selection_highlight_is_rendered(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    ti = play.new_text_input(value="hello", width=200, height=40)
    registry.focus(ti)
    ti.update()
    before = _image(ti)
    _press(ti, pygame.K_a, mod=CTRL)
    ti.update()
    assert _image(ti) != before


def test_placeholder_setter():
    ti = play.new_text_input(placeholder="old")
    before = _image(ti)
    ti.placeholder = "new"
    assert ti.placeholder == "new"
    ti.update()
    assert _image(ti) != before


def test_setting_the_text_colour_redraws_the_value():
    ti = play.new_text_input(value="hello")
    ti.text_color = "red"
    assert ti.text_color == "red"
    ti.update()
    assert count_color(ti.image, color_name_to_rgb("red")) > 0


def test_setting_the_placeholder_colour_redraws_the_placeholder():
    ti = play.new_text_input(placeholder="name")
    ti.placeholder_color = "purple"
    assert ti.placeholder_color == "purple"
    ti.update()
    assert count_color(ti.image, color_name_to_rgb("purple")) > 0


def test_a_bigger_font_size_draws_bigger_text():
    ti = play.new_text_input(value="Hi", text_color="red", height=80)
    small = count_color(ti.image, (255, 0, 0))
    ti.font_size = 40
    assert ti.font_size == 40
    ti.update()
    assert count_color(ti.image, (255, 0, 0)) > small
