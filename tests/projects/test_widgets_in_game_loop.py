"""Slider, Dropdown and TextInput driven through the real game loop.

The unit tests under tests/objects/ drive widgets by calling update() and the
click_at helper. These drive them the way a student's game does: real pygame
events through play.start_program(), so the whole frame path runs -- event
draining, keyboard suspension while a field is focused, physics sub-steps,
and update_sprites().

That path is where the widgets have actually broken before: a checkbox that
toggled ten times per click looked perfect to every single-update unit test.
"""

from tests.conftest import (
    post_mouse_motion,
    post_mouse_down,
    post_mouse_up,
    post_key_down,
    post_key_up,
)
from tests.projects.conftest import add_safety_timeout

max_frames = 400


def _screen_xy(screen, x, y):
    """Play-coordinates to pygame screen coordinates."""
    return int(screen.width / 2 + x), int(screen.height / 2 - y)


# ── Slider ────────────────────────────────────────────────────────────────────


def test_slider_drag_in_the_game_loop():
    import play
    from play.io.screen import screen

    values = []
    slider = play.new_slider(min_value=0, max_value=100, value=0, x=0, y=0, width=200)
    slider.when_changed(values.append)

    @play.when_program_starts
    async def driver():
        for _ in range(5):
            await play.animate()

        start = _screen_xy(screen, -90, 0)
        post_mouse_motion(*start)
        await play.animate()
        post_mouse_down(*start)
        await play.animate()

        for x in (-40, 0, 40, 90):
            post_mouse_motion(*_screen_xy(screen, x, 0))
            await play.animate()

        post_mouse_up(*_screen_xy(screen, 90, 0))
        await play.animate()
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert slider.value == 100, "dragging past the right edge should reach max_value"
    assert values, "when_changed should fire while dragging"
    assert values == sorted(values), "a left-to-right drag should only increase"
    assert slider._dragging is False, "releasing the mouse should end the drag"


def test_slider_ignores_mouse_motion_without_a_press():
    import play
    from play.io.screen import screen

    slider = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)

    @play.when_program_starts
    async def driver():
        for _ in range(5):
            await play.animate()
        for x in (-90, 0, 90):
            post_mouse_motion(*_screen_xy(screen, x, 0))
            await play.animate()
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert slider.value == 50, "hovering must not move the slider"


# ── Dropdown ──────────────────────────────────────────────────────────────────


def test_dropdown_selection_in_the_game_loop():
    import play
    from play.io.screen import screen

    received = []
    dd = play.new_dropdown(
        options=["Easy", "Normal", "Hard"], x=0, y=0, width=160, height=40
    )
    dd.when_changed(lambda value, index: received.append((value, index)))
    opened = []

    @play.when_program_starts
    async def driver():
        async def click(x, y):
            pos = _screen_xy(screen, x, y)
            post_mouse_motion(*pos)
            await play.animate()
            post_mouse_down(*pos)
            await play.animate()
            post_mouse_up(*pos)
            await play.animate()

        for _ in range(5):
            await play.animate()

        await click(0, 0)  # open the menu
        opened.append(dd.is_open)
        await click(0, -120)  # third option row
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert opened == [True], "clicking the closed button should open the menu"
    assert dd.is_open is False, "picking an option should close the menu"
    assert dd.selected_value == "Hard"
    assert received == [("Hard", 2)], "when_changed should fire exactly once"


# ── TextInput ─────────────────────────────────────────────────────────────────


def test_text_input_captures_the_keyboard_in_the_game_loop():
    import pygame
    import play
    from play.io.screen import screen
    from play.globals import globals_list

    game_keys = []
    submitted = []
    field = play.new_text_input(x=0, y=0, width=200, height=40)
    field.when_submit(submitted.append)
    seen = {}

    @play.when_key_pressed("a")
    def on_a(key=None):
        game_keys.append("a")

    @play.when_program_starts
    async def driver():
        async def press(pygame_key):
            post_key_down(pygame_key)
            await play.animate()
            await play.animate()
            post_key_up(pygame_key)
            await play.animate()

        for _ in range(5):
            await play.animate()

        # The game's own key callback works before anything is focused.
        await press(pygame.K_a)
        seen["before"] = len(game_keys)

        # Click the field to focus it.
        pos = _screen_xy(screen, 0, 0)
        post_mouse_motion(*pos)
        await play.animate()
        post_mouse_down(*pos)
        await play.animate()
        post_mouse_up(*pos)
        await play.animate()
        seen["focused"] = globals_list.focused_text_input is field

        # Typing reaches the field...
        pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, {"text": "hi"}))
        await play.animate()

        # ...and the game's key callback stays suspended while focused.
        await press(pygame.K_a)
        seen["during"] = len(game_keys)

        # Enter submits and blurs, so the game gets its keyboard back.
        post_key_down(pygame.K_RETURN)
        await play.animate()
        post_key_up(pygame.K_RETURN)
        await play.animate()
        seen["blurred"] = globals_list.focused_text_input is None

        await press(pygame.K_a)
        seen["after"] = len(game_keys)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert seen.get("focused") is True, "clicking the field should focus it"
    assert field.value == "hi", "typing should reach the focused field"
    assert submitted == ["hi"], "Enter should submit the current value"
    assert seen["blurred"] is True, "submitting should release focus"

    assert seen["before"] > 0, "the game's key callback should work when unfocused"
    assert (
        seen["during"] == seen["before"]
    ), "the game's key callback must stay suspended while a field is focused"
    assert seen["after"] > seen["during"], "blurring should restore the game's keyboard"


def test_tab_moves_focus_between_fields_in_the_game_loop():
    import pygame
    import play
    from play.io.screen import screen
    from play.globals import globals_list

    first = play.new_text_input(x=0, y=60, width=200, height=40)
    second = play.new_text_input(x=0, y=-60, width=200, height=40)
    seen = {}

    @play.when_program_starts
    async def driver():
        for _ in range(5):
            await play.animate()

        pos = _screen_xy(screen, 0, 60)
        post_mouse_motion(*pos)
        await play.animate()
        post_mouse_down(*pos)
        await play.animate()
        post_mouse_up(*pos)
        await play.animate()
        seen["first"] = globals_list.focused_text_input is first

        post_key_down(pygame.K_TAB)
        await play.animate()
        post_key_up(pygame.K_TAB)
        await play.animate()
        seen["second"] = globals_list.focused_text_input is second
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert seen.get("first") is True, "clicking the first field should focus it"
    assert seen["second"] is True, "Tab should move focus to the next field"
