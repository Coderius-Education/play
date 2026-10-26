"""Game controllers: reading them, and their button and axis events."""

import pygame
import pytest

from play.io import controllers as controllers_module
from play.io.controllers import controllers
from tests.events.frames import (
    axis_moved,
    button_down,
    button_up,
    play_frames,
)


class _Joystick:
    """A joystick whose every reading tells which device and which input was read."""

    def __init__(self, device_index):
        self.device_index = device_index

    def init(self):
        pass

    def get_instance_id(self):
        return 10 + self.device_index

    def get_numaxes(self):
        return 6 + self.device_index

    def get_axis(self, axis):
        return self.device_index + axis / 10

    def get_numbuttons(self):
        return 12 + self.device_index

    def get_button(self, button):
        return button == 3 + self.device_index

    def get_numhats(self):
        return 1 + self.device_index

    def get_hat(self, hat):
        return (hat, self.device_index)

    def get_numballs(self):
        return 2 + self.device_index

    def get_ball(self, ball):
        return (ball, self.device_index)


@pytest.fixture
def two_controllers(monkeypatch):
    """Two controllers plugged in before the game starts, SDL instance ids 10 and 11."""
    monkeypatch.setattr(controllers_module, "_Controller", _Joystick)
    monkeypatch.setattr(controllers_module, "_get_controller_count", lambda: 2)
    plugged_in = controllers_module._Controllers()
    monkeypatch.setattr(controllers, "_controllers", plugged_in._controllers)
    return plugged_in._controllers


def test_controllers_plugged_in_at_the_start_are_counted_in_order(two_controllers):
    assert controllers.get_count() == 2
    assert controllers.get_all_controllers() == two_controllers
    assert [controllers.get_controller(i).device_index for i in (0, 1)] == [0, 1]


def test_get_all_controllers_hands_out_a_copy(two_controllers):
    controllers.get_all_controllers().clear()

    assert controllers.get_count() == 2


def test_each_controller_is_read_input_by_input_from_its_own_device(two_controllers):
    def readings(index):
        return [
            controllers.get_num_axes(index),
            controllers.get_axis(index, 5),
            controllers.get_num_buttons(index),
            [controllers.get_button(index, b) for b in (3, 4)],
            controllers.get_num_hats(index),
            controllers.get_hat(index, 2),
            controllers.get_num_balls(index),
            controllers.get_ball(index, 1),
        ]

    assert readings(0) == [6, 0.5, 12, [True, False], 1, (2, 0), 2, (1, 0)]
    assert readings(1) == [7, 1.5, 13, [False, True], 2, (2, 1), 3, (1, 1)]


def test_when_button_pressed_fires_once_per_press_with_the_button():
    pressed = []
    controllers.when_button_pressed(0, 1, 2)(lambda button: pressed.append(button))

    play_frames(
        [button_down(2)], [], [button_down(3)], [button_up(2)], [button_down(1)]
    )

    assert pressed == [2, 1]


def test_when_button_released_fires_on_the_release_not_the_press():
    released = []
    controllers.when_button_released(0, 5)(lambda button: released.append(button))

    play_frames([button_down(5)], [], [], [button_up(5)])

    assert released == [5]


def test_button_callbacks_hear_their_own_controller_only(two_controllers):
    log = []
    controllers.when_button_pressed(1, 0, 1)(
        lambda button: log.append(("down", button))
    )
    controllers.when_button_released(1, 0, 1)(lambda button: log.append(("up", button)))

    play_frames(
        [button_down(0, instance_id=10)],
        [button_up(0, instance_id=10)],
        [button_down(1, instance_id=11)],
        [button_up(1, instance_id=11)],
    )

    assert log == [("down", 1), ("up", 1)]


@pytest.mark.xfail(
    strict=True,
    reason="when_any_button_pressed/released reject their own 'any' with a ValueError",
)
@pytest.mark.parametrize("released", [False, True], ids=["pressed", "released"])
def test_when_any_button_is_told_which_button(released):
    heard = []
    if released:
        decorator = controllers.when_any_button_released(0)
    else:
        decorator = controllers.when_any_button_pressed(0)
    decorator(lambda button: heard.append(button))

    play_frames([button_down(7)], [button_up(7)])

    assert heard == [7]


def test_when_axis_moved_reports_the_direction_as_minus_one_zero_or_one():
    values = []
    controllers.when_axis_moved(0, 1)(lambda axis, value: values.append(value))

    play_frames(
        [axis_moved(1, -0.8)],
        [axis_moved(1, 0.3)],
        [axis_moved(1, 0.6)],
        [axis_moved(0, 1.0)],
    )

    assert values == [-1, 0, 1]


def test_unplugging_a_controller_lets_go_of_its_held_buttons(two_controllers):
    held = []
    controllers.while_button_pressed(0, 0)(lambda button: held.append(button))

    play_frames(
        [button_down(0, instance_id=10)],
        [],
        [pygame.event.Event(pygame.JOYDEVICEREMOVED, {"instance_id": 10})],
        [],
        [],
    )

    assert held == [0, 0]


@pytest.mark.parametrize(
    "buttons", [("A",), ([1, "B"],)], ids=["name", "name in a list"]
)
@pytest.mark.parametrize(
    "decorator", [controllers.when_button_pressed, controllers.when_button_released]
)
def test_a_button_that_is_not_a_number_is_rejected(decorator, buttons):
    with pytest.raises(ValueError, match="must be an integer"):
        decorator(0, *buttons)
