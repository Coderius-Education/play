"""Tests for enhanced TextInput features: cursor movement, clipboard, disabled, password, tab."""

import pygame
import pytest
import play
from play.globals import globals_list
from play.objects.widgets import text_input_registry as registry
from play.utils import color_name_to_rgb
from tests.conftest import click_at, count_color, image_bytes
from tests.objects.clone_checks import BUNDLED_FONT, appearance, middle_of

CTRL = pygame.KMOD_CTRL


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key, mod=0):
    """A KEYDOWN event for *key* with modifier keys *mod*."""
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": ""})


def _press(field, *keys, mod=0):
    """Hand *field* a KEYDOWN for each of *keys*, all with modifier keys *mod*."""
    for key in keys:
        field._handle_keydown(_keydown(key, mod))


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


def test_backspace_on_a_field_emptied_by_deleting_the_selection_reports_nothing():
    ti = play.new_text_input(value="hello")
    changed = []
    ti.when_changed(changed.append)
    _press(ti, pygame.K_a, mod=CTRL)
    _press(ti, pygame.K_BACKSPACE, pygame.K_BACKSPACE)
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
    assert ti.value == "abc"


def test_a_password_field_draws_bullets_but_keeps_the_real_value():
    secret = play.new_text_input(value="secret", password_mode=True, x=0, y=100)
    bullets = play.new_text_input(value="••••••", x=0, y=-100)
    assert secret.value == "secret"
    assert image_bytes(secret) == image_bytes(bullets)


def test_turning_password_mode_on_masks_what_is_drawn():
    ti = play.new_text_input(value="secret", x=0, y=100)
    bullets = play.new_text_input(value="••••••", x=0, y=-100)
    assert image_bytes(ti) != image_bytes(bullets)
    ti.password_mode = True
    assert ti.password_mode is True
    ti.update()
    assert image_bytes(ti) == image_bytes(bullets)


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


def test_tab_from_a_still_focused_field_outside_the_tab_order_goes_to_the_first_field():
    a = play.new_text_input()
    play.new_text_input()
    c = play.new_text_input()
    registry.focus(c)
    c._is_disabled = True
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


def test_a_cloned_field_looks_like_the_original_but_starts_empty():
    ti = play.new_text_input(
        placeholder="name",
        value="secret",
        x=30,
        y=20,
        width=150,
        height=36,
        color="yellow",
        active_color="orange",
        text_color="blue",
        placeholder_color="purple",
        font_size=24,
        font=BUNDLED_FONT,
        border_color="green",
        border_width=3,
        border_radius=9,
        max_length=4,
        transparency=70,
        size=120,
        anchor="top-left",
        layer=12,
        readonly=True,
        password_mode=True,
    )
    c = ti.clone()
    assert c.value == ""
    assert (c.placeholder, c.readonly, c.password_mode) == ("name", True, True)
    ti.value = ""
    assert appearance(c) == appearance(ti)

    ti.value = c.value = "abcdef"
    assert c.value == "abcd"
    assert appearance(c) == appearance(ti)
    x, y = middle_of(ti)
    click_at(x, y, c)
    focused_twin = appearance(c)
    # The clone is drawn on top, so it would take the click meant for ti.
    c.hide()
    click_at(x, y, ti)
    assert appearance(ti) == focused_twin

    ti.disabled = True
    disabled_twin = ti.clone()
    disabled_twin.value = "abcdef"
    assert disabled_twin.disabled is True
    assert appearance(disabled_twin) == appearance(ti)


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
    def unavailable():
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", unavailable)
    ti = play.new_text_input(value="safe")
    _press(ti, pygame.K_v, mod=CTRL)
    assert ti.value == "safe"


def test_copy_survives_unavailable_scrap(monkeypatch):
    ti = play.new_text_input(value="hello")
    registry.focus(ti)

    def unavailable(*_args, **_kwargs):
        raise pygame.error("scrap not available")

    monkeypatch.setattr(pygame.scrap, "init", unavailable)
    _press(ti, pygame.K_a, pygame.K_c, mod=CTRL)
    assert ti.value == "hello"
    ti._handle_text_input("X")
    assert ti.value == "X"


def test_selection_highlight_is_rendered(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    ti = play.new_text_input(value="hello", width=200, height=40)
    registry.focus(ti)
    ti.update()
    before = image_bytes(ti)
    _press(ti, pygame.K_a, mod=CTRL)
    ti.update()
    assert image_bytes(ti) != before


def test_placeholder_setter():
    ti = play.new_text_input(placeholder="old")
    before = image_bytes(ti)
    ti.placeholder = "new"
    assert ti.placeholder == "new"
    ti.update()
    assert image_bytes(ti) != before


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
