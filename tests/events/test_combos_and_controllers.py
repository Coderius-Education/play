"""Key and button combinations, any-axis callbacks and controllers plugged in late (#244)."""

import pygame
import pytest

import play
from play.io.controllers import controllers


def _run(steps):
    """Run the game; each step is a list of events to post, one frame apart."""

    @play.when_program_starts
    async def driver():
        await play.animate()
        for events in steps:
            for event in events:
                pygame.event.post(event)
            await play.animate()
        for _ in range(3):
            await play.animate()
        play.stop_program()

    play.start_program()


def _down(key):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key})


def _up(key):
    return pygame.event.Event(pygame.KEYUP, {"key": key})


def test_a_key_combination_fires_when_its_last_key_goes_down():
    fired = []
    play.when_key_pressed(["a", "s"])(lambda: fired.append("a+s"))

    _run([[_down(pygame.K_a)], [], [_down(pygame.K_s)], [], [_up(pygame.K_s)]])

    assert fired == ["a+s"]


def test_a_key_combination_release_fires_once_when_one_of_its_keys_goes_up():
    fired = []
    play.when_key_released(["a", "s"])(lambda: fired.append("a+s"))

    _run(
        [
            [_down(pygame.K_a)],
            [_down(pygame.K_s)],
            [_up(pygame.K_s)],
            [],
            [_up(pygame.K_a)],
        ]
    )

    assert fired == ["a+s"]


def test_a_held_key_combination_keeps_firing_with_another_key_held_too():
    frames = []
    play.while_key_pressed(["a", "s"])(lambda: frames.append(1))

    _run([[_down(pygame.K_a), _down(pygame.K_s), _down(pygame.K_d)]] + [[]] * 5)

    assert len(frames) >= 5


def _joy(event_type, **attributes):
    return pygame.event.Event(event_type, attributes)


def test_when_any_axis_moved_fires():
    moved = []
    controllers.when_any_axis_moved(0)(lambda axis, value: moved.append((axis, value)))

    _run([[_joy(pygame.JOYAXISMOTION, instance_id=0, axis=1, value=1.0)]])

    assert moved == [(1, 1)]


def test_an_axis_callback_ignores_other_controllers():
    moved = []
    controllers.when_axis_moved(0, 1)(lambda axis, value: moved.append(value))

    _run([[_joy(pygame.JOYAXISMOTION, instance_id=1, axis=1, value=1.0)]])

    assert moved == []


class _FakeJoystick:
    """Stands in for a pygame Joystick whose SDL instance id is chosen by the test."""

    next_instance_id = 0

    def __init__(self, device_index):
        self.device_index = device_index
        self.instance_id = _FakeJoystick.next_instance_id

    def init(self):
        pass

    def get_instance_id(self):
        return self.instance_id


@pytest.fixture
def fake_joysticks(monkeypatch):
    monkeypatch.setattr("play.io.controllers._Controller", _FakeJoystick)
    monkeypatch.setattr(controllers, "_controllers", [])
    return _FakeJoystick


def test_a_controller_plugged_in_after_the_game_starts_works(fake_joysticks):
    fake_joysticks.next_instance_id = 5
    pressed = []
    controllers.when_button_pressed(0, 0)(lambda button: pressed.append(button))

    _run(
        [
            [_joy(pygame.JOYDEVICEADDED, device_index=0)],
            [_joy(pygame.JOYBUTTONDOWN, instance_id=5, button=0)],
        ]
    )

    assert controllers.get_count() == 1
    assert pressed == [0]


def test_a_replugged_controller_keeps_its_index(fake_joysticks):
    pressed = []
    controllers.when_button_pressed(0, 0)(lambda button: pressed.append(button))
    fake_joysticks.next_instance_id = 5
    controllers._connect(0)
    fake_joysticks.next_instance_id = 6

    _run(
        [
            [_joy(pygame.JOYDEVICEREMOVED, instance_id=5)],
            [_joy(pygame.JOYDEVICEADDED, device_index=0)],
            [_joy(pygame.JOYBUTTONDOWN, instance_id=6, button=0)],
        ]
    )

    assert controllers.get_count() == 1
    assert pressed == [0]
