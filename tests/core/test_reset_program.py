"""play.reset_program(): back to the state of a fresh import, for a playground or a test suite."""

import pygame
import pytest

import play
from play.globals import globals_list
from play.io.keypress import keyboard_state
from play.physics import physics_space, set_gravity


def _stop_on_the_first_frame(heard, name):
    """A repeat_forever callback that notes *name* in *heard* and stops the program."""

    def tick():
        heard.append(name)
        play.stop_program()

    return tick


def test_a_second_program_runs_after_a_reset_without_the_first_programs_callbacks():
    heard = []
    play.repeat_forever(_stop_on_the_first_frame(heard, "first"))
    play.start_program()

    play.reset_program()
    play.repeat_forever(_stop_on_the_first_frame(heard, "second"))
    play.start_program()

    assert heard == ["first", "second"]


def test_a_reset_puts_back_the_screen_physics_backdrop_and_event_queue():
    play.new_box(color="red", width=200, height=200)
    play.screen.width, play.screen.height = 300, 200
    play.screen.caption = "My game"
    play.screen.resizable = True
    set_gravity(vertical=-500, horizontal=20)
    play.set_backdrop("blue")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a}))

    play.reset_program()
    assert not pygame.event.peek(pygame.KEYDOWN)
    play.repeat_forever(play.stop_program)
    play.start_program()

    assert play.screen.size == (800, 600)
    assert play.screen.caption == "coderius-play"
    assert play.screen.resizable is False
    assert tuple(physics_space.gravity) == (0, -100)
    assert globals_list.display.get_at((400, 300))[:3] == (255, 255, 255)
    assert len(globals_list.walls) == 4


def test_a_reset_forgets_keys_and_clicks_held_in_the_last_program():
    play.mouse._is_clicked = True
    keyboard_state.pressed.add("a")

    play.reset_program()

    assert not play.mouse.is_clicked
    assert not play.key_is_pressed("a")


def test_a_reset_while_the_program_runs_is_refused_and_changes_nothing():
    refused = []

    @play.repeat_forever
    def try_to_reset():
        try:
            play.reset_program()
        except RuntimeError as error:
            refused.append((str(error), globals_list.program_state))
        play.stop_program()

    play.start_program()

    ((message, state_after),) = refused
    assert "while the program is running" in message
    assert state_after is play.globals.ProgramState.RUNNING


def test_a_script_that_never_started_does_not_keep_the_next_one_from_starting(
    run_script,
):
    printed = run_script(
        "try:\n"
        "    play.new_circle()\n"
        "    play.when_program_starts(lambda: print('old'))\n"
        "    raise NameError('a typo after new_circle')\n"
        "except NameError:\n"
        "    play.reset_program()\n"
        "\n"
        "@play.when_program_starts\n"
        "def started():\n"
        "    print('started')\n"
        "    os._exit(0)\n"
    )

    assert printed == ["started"]
