import pygame
import pytest
import play
from play.globals import globals_list
from play.objects.widgets import text_input_registry as registry
from play.utils import color_name_to_rgb
from tests.conftest import click_at, count_color


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": ""})


# ── creation ────────────────────────────────────────────────────────────────


def test_text_input_creation():
    ti = play.new_text_input(placeholder="Type here", value="hello")
    assert ti.value == "hello"
    assert ti.placeholder == "Type here"
    assert ti.layer == 10
    assert ti.image.get_size() == (200, 40)


def test_a_new_field_is_empty_and_does_not_take_the_keyboard():
    ti = play.new_text_input()
    assert ti.value == ""
    assert globals_list.focused_text_input is None


# ── value property ───────────────────────────────────────────────────────────


def test_value_setter():
    ti = play.new_text_input()
    before = pygame.image.tobytes(ti.image, "RGBA")
    ti.value = "abc"
    assert ti.value == "abc"
    ti.update()
    assert pygame.image.tobytes(ti.image, "RGBA") != before


def test_setting_a_number_as_the_value_shows_it_as_text():
    ti = play.new_text_input()
    ti.value = 42
    ti.update()
    assert ti.value == "42"
    ti._handle_text_input("!")
    assert ti.value == "42!"


def test_typing_after_setting_the_value_appends_to_it():
    ti = play.new_text_input(value="abcdef")
    registry.focus(ti)
    ti._handle_keydown(_keydown(pygame.K_HOME))
    ti.value = "xy"
    ti._handle_text_input("z")
    assert ti.value == "xyz"


def test_value_setter_fires_callbacks():
    ti = play.new_text_input()
    received = []
    ti.when_changed(received.append)
    ti.value = "hello"
    assert received == ["hello"]


# ── keyboard input ───────────────────────────────────────────────────────────


def test_text_input_appends_characters():
    ti = play.new_text_input()
    ti._handle_text_input("h")
    ti._handle_text_input("i")
    assert ti.value == "hi"


def test_backspace_removes_last_char():
    ti = play.new_text_input(value="abc")
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "ab"


def test_backspace_on_empty_is_noop():
    ti = play.new_text_input()
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == ""


def test_max_length_respected():
    ti = play.new_text_input(max_length=3)
    ti._handle_text_input("hello")
    assert ti.value == "hel"


def test_max_length_exact_boundary():
    ti = play.new_text_input(max_length=2)
    ti._handle_text_input("ab")
    ti._handle_text_input("c")
    assert ti.value == "ab"


def test_max_length_enforced_by_constructor():
    ti = play.new_text_input(value="x" * 100, max_length=5)
    assert ti.value == "xxxxx"


def test_max_length_enforced_by_value_setter():
    ti = play.new_text_input(max_length=5)
    ti.value = "y" * 100
    assert ti.value == "yyyyy"


# ── callbacks ────────────────────────────────────────────────────────────────


def test_when_changed_fires_on_input():
    ti = play.new_text_input()
    received = []

    @ti.when_changed
    def on_change(v):
        received.append(v)

    ti._handle_text_input("x")
    ti._handle_text_input("y")
    assert received == ["x", "xy"]


def test_when_changed_fires_on_backspace():
    ti = play.new_text_input(value="ab")
    received = []
    ti.when_changed(received.append)
    ti._handle_keydown(_keydown(pygame.K_BACKSPACE))
    assert received == ["a"]


def test_when_submit_fires_on_enter():
    ti = play.new_text_input(value="done")
    submitted = []
    ti.when_submit(submitted.append)
    ti._handle_keydown(_keydown(pygame.K_RETURN))
    assert submitted == ["done"]


def test_when_submit_fires_on_numpad_enter():
    ti = play.new_text_input(value="ok")
    submitted = []
    ti.when_submit(submitted.append)
    ti._handle_keydown(_keydown(pygame.K_KP_ENTER))
    assert submitted == ["ok"]


def test_when_changed_rejects_async():
    ti = play.new_text_input()
    with pytest.raises(TypeError, match="async"):

        @ti.when_changed
        async def on_change(v):
            pass


def test_when_submit_rejects_async():
    ti = play.new_text_input()
    with pytest.raises(TypeError, match="async"):

        @ti.when_submit
        async def on_submit(v):
            pass


# ── focus management ─────────────────────────────────────────────────────────


def test_focus_sets_is_focused():
    ti = play.new_text_input()
    registry.focus(ti)
    assert ti._is_focused is True
    assert globals_list.focused_text_input is ti


def test_clear_focus_blurs_widget():
    ti = play.new_text_input()
    registry.focus(ti)
    registry.clear_focus()
    assert globals_list.focused_text_input is None
    assert ti._is_focused is False


def test_escape_clears_focus():
    ti = play.new_text_input()
    registry.focus(ti)
    ti._handle_keydown(_keydown(pygame.K_ESCAPE))
    assert globals_list.focused_text_input is None


def test_focusing_another_blurs_previous():
    a = play.new_text_input(x=-100)
    b = play.new_text_input(x=100)

    registry.focus(a)
    registry.focus(b)

    assert globals_list.focused_text_input is b
    assert a._is_focused is False


# ── alive & layer ────────────────────────────────────────────────────────────


def test_text_input_alive():
    ti = play.new_text_input()
    assert ti.alive()


def test_text_input_layer():
    ti = play.new_text_input(layer=15)
    assert ti.layer == 15
    assert globals_list.sprites_group.get_layer_of_sprite(ti) == 15


# ── update() click paths ─────────────────────────────────────────────────────


def test_clicking_input_gains_focus():
    ti = play.new_text_input(x=0, y=0, width=100, height=40)
    click_at(0, 0, ti)
    assert ti._is_focused is True
    assert globals_list.focused_text_input is ti


def test_clicking_back_into_a_field_puts_the_cursor_at_the_end():
    ti = play.new_text_input(value="abc", x=0, y=0)
    click_at(0, 0, ti)
    ti._handle_keydown(_keydown(pygame.K_HOME))
    click_at(300, 250, ti)
    click_at(0, 0, ti)
    ti._handle_text_input("X")
    assert ti.value == "abcX"


def test_clicking_elsewhere_blurs_focused_input():
    ti = play.new_text_input(x=0, y=0)
    registry.focus(ti)
    click_at(9999, 9999, ti)
    assert ti._is_focused is False
    assert globals_list.focused_text_input is None


def test_clicking_a_button_blurs_the_focused_input():
    ti = play.new_text_input(x=0, y=100)
    button = play.new_button("Start", x=0, y=-100)
    registry.focus(ti)

    click_at(0, -100, ti, button)

    assert ti._is_focused is False
    assert globals_list.focused_text_input is None


@pytest.mark.parametrize("first", ["a", "b"])
def test_clicking_another_input_moves_the_focus(first):
    # Both update orders: the old field must not clear the new one's focus.
    a = play.new_text_input(x=0, y=100)
    b = play.new_text_input(x=0, y=-100)
    registry.focus(a)

    order = (a, b) if first == "a" else (b, a)
    click_at(0, -100, *order)

    assert globals_list.focused_text_input is b
    assert a._is_focused is False


# ── _blit_input_text branches ────────────────────────────────────────────────


def test_blit_placeholder_when_empty_and_unfocused():
    # Not "gray": that is also the default border colour, so the count would
    # include border pixels and could never fall to zero.
    placeholder_rgb = color_name_to_rgb("magenta")
    ti = play.new_text_input(placeholder="Type here", placeholder_color="magenta")
    ti.update()
    assert count_color(ti.image, placeholder_rgb) > 0  # placeholder is drawn

    # Once there is a value, the placeholder must be gone entirely.
    ti.value = "typed"
    ti.update()
    assert count_color(ti.image, placeholder_rgb) == 0


def test_the_placeholder_disappears_while_the_field_is_focused():
    magenta = color_name_to_rgb("magenta")
    ti = play.new_text_input(
        placeholder="Type here", placeholder_color="magenta", x=0, y=0
    )
    click_at(0, 0, ti)
    assert count_color(ti.image, magenta) == 0


def test_blit_cursor_when_focused_and_visible(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    ti = play.new_text_input()
    registry.focus(ti)

    ti._cursor_visible = True
    ti.update()
    with_cursor = pygame.image.tobytes(ti.image, "RGBA")

    ti._cursor_visible = False
    ti.update()
    without_cursor = pygame.image.tobytes(ti.image, "RGBA")

    # The blink has to be visible, not merely non-crashing.
    assert with_cursor != without_cursor


def test_an_unfocused_field_shows_no_caret(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    red = color_name_to_rgb("red")
    ti = play.new_text_input(x=0, y=0, text_color="red")
    ti.update()
    assert count_color(ti.image, red) == 0
    click_at(0, 0, ti)
    assert count_color(ti.image, red) > 0


def test_blit_long_text_clips_to_box_width():
    ti = play.new_text_input(width=80)
    empty_width = ti.image.get_width()

    ti.value = "a" * 60
    ti.update()
    # Overflowing text must be clipped inside the field, not widen it.
    assert ti.image.get_width() == empty_width


def test_a_long_value_scrolls_so_its_end_is_visible_while_typing(monkeypatch):
    monkeypatch.setattr(pygame.time, "get_ticks", lambda: 0)
    first = play.new_text_input(value="a" * 59 + "W", width=80, x=0, y=100)
    second = play.new_text_input(value="a" * 60, width=80, x=0, y=-100)
    for field in (first, second):
        registry.focus(field)
        field.update()
    assert pygame.image.tobytes(first.image, "RGBA") != pygame.image.tobytes(
        second.image, "RGBA"
    )


# ── remove() ─────────────────────────────────────────────────────────────────


def test_remove_clears_focus():
    ti = play.new_text_input()
    registry.focus(ti)
    ti.remove()
    assert globals_list.focused_text_input is None


# ── registry dispatch ─────────────────────────────────────────────────────────


def test_dispatch_text_reaches_focused_widget():
    ti = play.new_text_input()
    registry.focus(ti)
    registry.dispatch_text("hi")
    assert ti.value == "hi"


def test_dispatch_keydown_reaches_focused_widget():
    ti = play.new_text_input(value="abc")
    registry.focus(ti)
    registry.dispatch_keydown(_keydown(pygame.K_BACKSPACE))
    assert ti.value == "ab"


def test_dispatch_text_no_focused_is_noop():
    ti = play.new_text_input(value="abc")  # exists but is not focused
    registry.dispatch_text("x")  # must not raise
    assert ti.value == "abc"  # and must not reach an unfocused field


def test_dispatch_keydown_no_focused_is_noop():
    ti = play.new_text_input(value="abc")
    registry.dispatch_keydown(_keydown(pygame.K_BACKSPACE))  # must not raise
    assert ti.value == "abc"


# ── focus and the keyboard ────────────────────────────────────────────────────


def test_enter_blurs_field_after_submit():
    # Regression: Enter fired when_submit but left the field focused, so the
    # game's keyboard callbacks stayed suspended after submitting.
    ti = play.new_text_input(value="done")
    registry.focus(ti)
    ti._handle_keydown(_keydown(pygame.K_RETURN))
    assert globals_list.focused_text_input is None
    assert ti._is_focused is False


def test_hide_releases_focus():
    # Regression: hiding a focused field left it focused, so an invisible
    # field kept exclusive keyboard capture.
    ti = play.new_text_input()
    registry.focus(ti)
    ti.hide()
    assert globals_list.focused_text_input is None
    assert ti._is_focused is False


def test_focusing_a_field_forgets_keys_held_before_it():
    from play.io.keypress import keyboard_state

    keyboard_state.pressed.add("right")
    keyboard_state.pressed_this_frame.add("right")
    registry.focus(play.new_text_input())
    assert not keyboard_state.pressed
    assert not keyboard_state.pressed_this_frame


def test_focus_turns_text_input_on_and_blur_turns_it_off(monkeypatch):
    calls = []
    monkeypatch.setattr(pygame.key, "start_text_input", lambda: calls.append("on"))
    monkeypatch.setattr(pygame.key, "stop_text_input", lambda: calls.append("off"))
    ti = play.new_text_input()
    registry.focus(ti)
    registry.clear_focus()
    assert calls == ["on", "off"]
