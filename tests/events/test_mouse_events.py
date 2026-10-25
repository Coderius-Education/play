"""Mouse clicks, releases and movement, through the real game loop."""

import itertools

import pygame
import pytest

import play
from play.io.screen import screen
from tests.events.frames import mouse_down, mouse_move, mouse_up, play_frames


def test_when_mouse_clicked_fires_once_per_click_however_long_it_is_held():
    clicks = []
    play.when_mouse_clicked(lambda: clicks.append(True))

    play_frames([mouse_down()], [], [], [mouse_up()], [mouse_down(), mouse_up()])

    assert clicks == [True, True]


def test_when_click_released_fires_when_the_button_goes_up():
    log = []
    play.when_mouse_clicked(lambda: log.append("clicked"))
    play.when_click_released(lambda: log.append("released"))

    play_frames([mouse_down(50, 50)], [], [mouse_up(-200, 100)])

    assert log == ["clicked", "released"]


def test_mouse_is_clicked_while_the_button_is_held():
    held = []
    play.repeat_forever(lambda: held.append(play.mouse.is_clicked))

    play_frames([], [mouse_down()], [], [mouse_up()])

    assert [state for state, _ in itertools.groupby(held)] == [False, True, False]


@pytest.mark.parametrize("button", [4, 5], ids=["wheel up", "wheel down"])
def test_scrolling_the_mouse_wheel_is_not_a_click(button):
    log = []
    play.when_mouse_clicked(lambda: log.append("clicked"))
    play.when_click_released(lambda: log.append("released"))

    @play.repeat_forever
    def watch():
        if play.mouse.is_clicked:
            log.append("held")

    play_frames([mouse_down(button=button), mouse_up(button=button)], [])

    assert log == []


def test_the_mouse_position_is_in_play_coordinates():
    seen = []

    @play.repeat_forever
    def track():
        seen.append((play.mouse.x, play.mouse.y))

    play_frames([mouse_move(120, -80)], [])

    assert seen[-1] == (120, -80)


def test_a_click_moves_the_mouse_to_where_it_happened():
    where = []
    play.when_mouse_clicked(lambda: where.append((play.mouse.x, play.mouse.y)))

    play_frames([mouse_down(-150, 75)])

    assert where == [(-150, 75)]


def test_a_click_without_mouse_motion_lands_where_it_was_made():
    box = play.new_box(x=150, y=100, width=60, height=60)
    clicked = []
    box.when_clicked(lambda: clicked.append(1))
    pos = (int(screen.width / 2 + 150), int(screen.height / 2 - 100))

    @play.when_program_starts
    async def click():
        await play.animate()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1))
        await play.animate()
        pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, pos=pos, button=1))
        for _ in range(3):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert clicked == [1]
