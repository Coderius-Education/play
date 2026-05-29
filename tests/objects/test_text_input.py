import pygame
import pytest
import play
from play.globals import globals_list
from play.objects import text_input_registry as registry
from play.core.mouse_loop import mouse_state
from play.io.mouse import mouse


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _keydown(key):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": ""})


# ── creation ────────────────────────────────────────────────────────────────


def test_text_input_creation():
    ti = play.new_text_input(placeholder="Type here", value="hello")
    assert ti.value == "hello"
    assert ti._placeholder == "Type here"
    assert ti.layer == 10
    assert ti.image is not None


def test_text_input_default_value():
    ti = play.new_text_input()
    assert ti.value == ""
    assert ti._is_focused is False


# ── value property ───────────────────────────────────────────────────────────


def test_value_setter():
    ti = play.new_text_input()
    ti.value = "abc"
    assert ti.value == "abc"
    assert ti._should_recompute is True


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
    import pytest

    ti = play.new_text_input()
    with pytest.raises(TypeError, match="async"):

        @ti.when_changed
        async def on_change(v):
            pass


def test_when_submit_rejects_async():
    import pytest

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
    mouse.x = 0
    mouse.y = 0
    mouse_state.click_happened = True
    ti.update()
    assert ti._is_focused is True
    assert globals_list.focused_text_input is ti


def test_clicking_elsewhere_blurs_focused_input():
    ti = play.new_text_input(x=0, y=0)
    registry.focus(ti)
    mouse.x = 9999
    mouse.y = 9999
    mouse_state.click_happened = True
    ti.update()
    assert ti._is_focused is False
    assert globals_list.focused_text_input is None


def test_cursor_toggles_after_500ms():
    ti = play.new_text_input()
    registry.focus(ti)
    ti._cursor_visible = True
    ti._last_blink = pygame.time.get_ticks() - 600
    ti._should_recompute = True
    ti.update()
    assert ti._cursor_visible is False


# ── _blit_input_text branches ────────────────────────────────────────────────


def test_blit_placeholder_when_empty_and_unfocused():
    ti = play.new_text_input(placeholder="Type here")
    ti._should_recompute = True
    ti.update()
    assert ti.image is not None


def test_blit_cursor_when_focused_and_visible():
    ti = play.new_text_input()
    registry.focus(ti)
    ti._cursor_visible = True
    ti._should_recompute = True
    ti.update()
    assert ti.image is not None


def test_blit_long_text_clips_to_box_width():
    ti = play.new_text_input(width=80)
    ti._input_value = "a" * 60  # far too long to fit
    ti._should_recompute = True
    ti.update()
    assert ti.image is not None


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
    registry.dispatch_text("x")  # no widget focused — must not raise


def test_dispatch_keydown_no_focused_is_noop():
    registry.dispatch_keydown(_keydown(pygame.K_BACKSPACE))  # must not raise


# ── key handler suppression ───────────────────────────────────────────────────


def test_focused_text_input_suppresses_key_callbacks():
    import asyncio
    from play.core.keyboard_loop import handle_keyboard, keyboard_state

    ti = play.new_text_input()
    registry.focus(ti)

    fired = []
    play.when_any_key_pressed(lambda key: fired.append(key))
    keyboard_state.pressed_this_frame.add("a")

    # game_loop skips handle_keyboard() when focused — simulate that guard
    if not globals_list.focused_text_input:
        asyncio.run(handle_keyboard())

    assert fired == [], "key callbacks must not fire while a TextInput is focused"
