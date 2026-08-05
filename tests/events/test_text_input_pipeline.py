"""Integration tests for the TextInput keyboard pipeline through the real game loop.

These tests post REAL pygame events (``pygame.event.post``) and run the actual
game loop via ``play.start_program()``, verifying the full path:

    event queue -> _handle_pygame_events -> text_input_registry dispatch
    -> TextInput handlers

including the keyboard-suppression contract: while a TextInput is focused,
``@play.when_key_pressed`` callbacks must NOT fire; after blur they must fire
again.

Each test registers a ``@play.repeat_forever`` driver that counts frames,
posts events on specific frames, records observations into a results dict, and
stops the program within a handful of frames. Events posted during the
repeat_forever callback of frame N are processed at the start of frame N+1.
"""

import sys

import pygame
import pytest

sys.path.insert(0, ".")

from conftest import post_mouse_down, post_mouse_motion, post_mouse_up

import play
from play.globals import globals_list
from play.objects import text_input_registry as registry


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _post_keydown(key, unicode=""):
    """Post a real KEYDOWN event as SDL would deliver it."""
    pygame.event.post(
        pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": unicode})
    )


def _post_textinput(text):
    """Post a real TEXTINPUT event as SDL would deliver it while typing."""
    pygame.event.post(pygame.event.Event(pygame.TEXTINPUT, {"text": text}))


def test_typing_updates_value_and_suppresses_keyboard_callbacks():
    """Clicking a TextInput focuses it; a posted TEXTINPUT event lands in its
    value, and a KEYDOWN posted while focused does NOT reach when_key_pressed."""
    ti = play.new_text_input(value="", x=0, y=0, width=200, height=40)

    key_presses = []
    results = {}
    frames = [0]

    @play.when_key_pressed("a")
    def on_a(key=None):  # pylint: disable=unused-argument
        key_presses.append(key)

    @play.repeat_forever
    def driver():
        frames[0] += 1
        if frames[0] == 1:
            # Click the centre of the TextInput (play (0,0) -> screen (400,300)).
            post_mouse_motion(400, 300)
            post_mouse_down(400, 300)
            post_mouse_up(400, 300)
        elif frames[0] == 2:
            # The click was processed at the start of this frame and the sprite
            # pass ran before repeat_forever callbacks, so focus is set now.
            results["focused_after_click"] = globals_list.focused_text_input is ti
            # Real typing delivers both a KEYDOWN and a TEXTINPUT event.
            _post_keydown(pygame.K_a, unicode="a")
            _post_textinput("a")
        elif frames[0] == 4:
            results["value"] = ti.value
            results["key_presses"] = list(key_presses)
            results["still_focused"] = globals_list.focused_text_input is ti
            play.stop_program()

    play.start_program()

    assert results["focused_after_click"] is True
    assert results["value"] == "a"
    # Keyboard suppression: the game callback must not have fired while focused.
    assert results["key_presses"] == []
    assert results["still_focused"] is True


def test_enter_submits_blurs_and_keyboard_callbacks_resume():
    """A posted Enter KEYDOWN fires when_submit once and blurs the field; a key
    posted on a later frame reaches when_key_pressed again."""
    ti = play.new_text_input(value="hello")
    registry.focus(ti)

    submitted = []
    key_presses = []
    results = {}
    frames = [0]

    @ti.when_submit
    def on_submit(value):
        submitted.append(value)

    @play.when_key_pressed("b")
    def on_b(key=None):  # pylint: disable=unused-argument
        key_presses.append(key)

    @play.repeat_forever
    def driver():
        frames[0] += 1
        if frames[0] == 1:
            _post_keydown(pygame.K_RETURN, unicode="\r")
        elif frames[0] == 2:
            results["submitted"] = list(submitted)
            results["focused_after_enter"] = globals_list.focused_text_input
            # Now that the field is blurred, this key must reach the game again.
            _post_keydown(pygame.K_b, unicode="b")
        elif frames[0] == 4:
            results["key_presses"] = list(key_presses)
            play.stop_program()

    play.start_program()

    assert results["submitted"] == ["hello"]
    assert results["focused_after_enter"] is None
    # After the blur, the posted key DID reach the game callback (exactly once —
    # pressed_this_frame semantics, and no KEYUP was posted).
    assert results["key_presses"] == ["b"]


def test_tab_cycles_focus_between_text_inputs():
    """Posted Tab KEYDOWN events move focus ti1 -> ti2 -> (wrap) ti1."""
    ti1 = play.new_text_input(x=-150, y=0)
    ti2 = play.new_text_input(x=150, y=0)
    registry.focus(ti1)

    results = {}
    frames = [0]

    @play.repeat_forever
    def driver():
        frames[0] += 1
        if frames[0] == 1:
            _post_keydown(pygame.K_TAB, unicode="\t")
        elif frames[0] == 2:
            results["after_first_tab"] = globals_list.focused_text_input
            _post_keydown(pygame.K_TAB, unicode="\t")
        elif frames[0] == 3:
            results["after_second_tab"] = globals_list.focused_text_input
            play.stop_program()

    play.start_program()

    assert results["after_first_tab"] is ti2
    # Tab order wraps around back to the first field.
    assert results["after_second_tab"] is ti1
