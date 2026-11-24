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


def test_a_sprite_clicked_without_any_mouse_motion_hears_the_click():
    box = play.new_box(x=150, y=100, width=60, height=60)
    clicked = []
    box.when_clicked(lambda: clicked.append(1))

    play_frames([mouse_down(150, 100)], [mouse_up(150, 100)])

    assert clicked == [1]


LEFT, MIDDLE, RIGHT, BACK, FORWARD = 1, 2, 3, 6, 7


def test_when_mouse_clicked_with_a_button_fires_only_for_that_button():
    clicks = []
    play.when_mouse_clicked("right")(lambda button: clicks.append(button))

    play_frames(
        [mouse_down(button=LEFT)],
        [mouse_up(button=LEFT)],
        [mouse_down(button=RIGHT)],
        [mouse_up(button=RIGHT)],
    )

    assert clicks == ["right"]


def test_when_mouse_clicked_fires_for_each_of_its_buttons():
    clicks = []
    play.when_mouse_clicked("left", "middle")(lambda button: clicks.append(button))

    play_frames(
        [mouse_down(button=MIDDLE), mouse_up(button=MIDDLE)],
        [mouse_down(button=RIGHT), mouse_up(button=RIGHT)],
        [mouse_down(button=LEFT), mouse_up(button=LEFT)],
    )

    assert clicks == ["middle", "left"]


def test_when_mouse_clicked_with_a_button_may_leave_out_the_button_parameter():
    clicks = []
    play.when_mouse_clicked("left")(lambda: clicks.append(True))

    play_frames([mouse_down(button=LEFT)], [mouse_up(button=LEFT)])

    assert clicks == [True]


def test_when_mouse_clicked_with_a_list_fires_when_the_buttons_are_held_together():
    clicks = []
    play.when_mouse_clicked(["left", "right"])(lambda: clicks.append(True))

    play_frames(
        [mouse_down(button=LEFT)],
        [mouse_up(button=LEFT)],
        [mouse_down(button=LEFT)],
        [mouse_down(button=RIGHT)],
        [mouse_up(button=RIGHT), mouse_up(button=LEFT)],
    )

    assert clicks == [True]


def test_when_click_released_with_a_button_fires_only_for_that_button():
    released = []
    play.when_click_released("left")(lambda button: released.append(button))

    play_frames(
        [mouse_down(button=RIGHT)],
        [mouse_up(button=RIGHT)],
        [mouse_down(button=LEFT)],
        [mouse_up(button=LEFT)],
    )

    assert released == ["left"]


def test_the_bare_decorators_still_fire_for_every_button():
    log = []
    play.when_mouse_clicked(lambda: log.append("clicked"))
    play.when_click_released(lambda: log.append("released"))

    play_frames([mouse_down(button=RIGHT)], [mouse_up(button=RIGHT)])

    assert log == ["clicked", "released"]


def test_the_mouse_object_takes_button_names_too():
    log = []
    play.mouse.when_clicked("middle")(lambda button: log.append(("clicked", button)))
    play.mouse.when_click_released("middle")(
        lambda button: log.append(("released", button))
    )

    play_frames(
        [mouse_down(button=LEFT), mouse_up(button=LEFT)],
        [mouse_down(button=MIDDLE)],
        [mouse_up(button=MIDDLE)],
    )

    assert log == [("clicked", "middle"), ("released", "middle")]


@pytest.mark.parametrize(
    "buttons",
    [(), ("wheel",), (1,), (["left", "x3"],), ([],)],
    ids=["nothing", "unknown name", "number", "unknown in a list", "empty list"],
)
@pytest.mark.parametrize(
    "decorator",
    [play.when_mouse_clicked, play.when_click_released, play.while_mouse_pressed],
    ids=["when_mouse_clicked", "when_click_released", "while_mouse_pressed"],
)
def test_mouse_decorators_reject_anything_but_button_names(decorator, buttons):
    with pytest.raises(ValueError, match="(?i)mouse button"):
        decorator(*buttons)


def test_the_side_buttons_are_named_back_and_forward():
    log = []
    play.when_mouse_clicked("back", "forward")(lambda button: log.append(button))
    play.when_click_released("forward")(lambda button: log.append(f"{button} up"))

    play_frames(
        [mouse_down(button=BACK), mouse_up(button=BACK)],
        [mouse_down(button=FORWARD)],
        [mouse_up(button=FORWARD)],
    )

    assert log == ["back", "forward", "forward up"]


def test_while_mouse_pressed_fires_while_a_side_button_is_held():
    held = []
    play.while_mouse_pressed("back")(lambda button: held.append(button))

    play_frames([mouse_down(button=BACK)], [], [mouse_up(button=BACK)])

    assert held == ["back"] * 2
