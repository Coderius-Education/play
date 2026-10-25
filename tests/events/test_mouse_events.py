"""Mouse clicks, releases and movement, through the real game loop."""

import itertools

import pytest

import play
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
