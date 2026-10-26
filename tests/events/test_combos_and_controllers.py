"""Key and button combinations, any-axis callbacks and controllers plugged in late (#244)."""

import pygame
import pytest

import play
from play.io.controllers import controllers
from tests.events.frames import key_down as _down, key_up as _up, play_frames


def test_a_key_combination_fires_when_its_last_key_goes_down():
    fired = []
    play.when_key_pressed(["a", "s"])(lambda: fired.append("a+s"))

    play_frames([_down(pygame.K_a)], [], [_down(pygame.K_s)], [], [_up(pygame.K_s)])

    assert fired == ["a+s"]


def test_a_key_combination_release_fires_once_when_one_of_its_keys_goes_up():
    fired = []
    play.when_key_released(["a", "s"])(lambda: fired.append("a+s"))

    play_frames(
        [_down(pygame.K_a)],
        [_down(pygame.K_s)],
        [_up(pygame.K_s)],
        [],
        [_up(pygame.K_a)],
    )

    assert fired == ["a+s"]


def test_a_key_combination_fires_for_a_key_tapped_within_one_frame():
    fired = []
    play.when_key_pressed(["left ctrl", "s"])(lambda: fired.append("ctrl+s"))

    play_frames([_down(pygame.K_LCTRL)], [_down(pygame.K_s), _up(pygame.K_s)])

    assert fired == ["ctrl+s"]


def test_a_held_key_combination_does_not_fire_again_for_an_extra_key():
    fired = []
    play.when_key_pressed(["a", "s"])(lambda: fired.append("pressed"))
    play.when_key_released(["a", "s"])(lambda: fired.append("released"))

    play_frames(
        [_down(pygame.K_a), _down(pygame.K_s)],
        [],
        [_down(pygame.K_d)],
        [_up(pygame.K_d)],
    )

    assert fired == ["pressed"]


def test_a_held_key_combination_fires_every_frame_with_another_key_held_too():
    held_frames = 6
    frames = []
    play.while_key_pressed(["a", "s"])(lambda: frames.append(1))

    play_frames(
        [_down(pygame.K_a), _down(pygame.K_s), _down(pygame.K_d)],
        *[[]] * (held_frames - 1),
        [_up(pygame.K_a)],
    )

    assert len(frames) == held_frames


def _joy(event_type, **attributes):
    return pygame.event.Event(event_type, attributes)


def test_when_any_axis_moved_fires():
    moved = []
    controllers.when_any_axis_moved(0)(lambda axis, value: moved.append((axis, value)))

    play_frames([_joy(pygame.JOYAXISMOTION, instance_id=0, axis=1, value=1.0)])

    assert moved == [(1, 1)]


def test_an_axis_callback_hears_its_own_controller_only():
    moved = []
    controllers.when_axis_moved(1, 1)(lambda axis, value: moved.append(value))

    play_frames(
        [_joy(pygame.JOYAXISMOTION, instance_id=1, axis=1, value=1.0)],
        [_joy(pygame.JOYAXISMOTION, instance_id=0, axis=1, value=-1.0)],
    )

    assert moved == [1]


class _FakeJoystick:
    next_instance_id = 0

    def __init__(self, device_index):
        self.device_index = device_index
        self.instance_id = _FakeJoystick.next_instance_id

    def init(self):
        pass

    def get_instance_id(self):
        return self.instance_id

    def get_axis(self, _axis):
        return 0.75


@pytest.fixture
def fake_joysticks(monkeypatch):
    monkeypatch.setattr("play.io.controllers._Controller", _FakeJoystick)
    monkeypatch.setattr(controllers, "_controllers", [])
    return _FakeJoystick


def test_a_controller_plugged_in_after_the_game_starts_gets_index_0(fake_joysticks):
    fake_joysticks.next_instance_id = 5
    pressed = []
    controllers.when_button_pressed(0, 0)(lambda button: pressed.append(button))

    play_frames(
        [_joy(pygame.JOYDEVICEADDED, device_index=0)],
        [_joy(pygame.JOYBUTTONDOWN, instance_id=5, button=0)],
    )

    assert controllers.get_count() == 1
    assert pressed == [0]


def test_a_replugged_controller_keeps_its_index(fake_joysticks):
    pressed = []
    controllers.when_button_pressed(0, 0)(lambda button: pressed.append(button))
    fake_joysticks.next_instance_id = 5
    controllers._connect(0)
    fake_joysticks.next_instance_id = 6

    play_frames(
        [_joy(pygame.JOYDEVICEREMOVED, instance_id=5)],
        [_joy(pygame.JOYDEVICEADDED, device_index=0)],
        [_joy(pygame.JOYBUTTONDOWN, instance_id=6, button=0)],
    )

    assert controllers.get_count() == 1
    assert pressed == [0]


def test_an_unplugged_controller_reads_as_untouched(fake_joysticks):
    fake_joysticks.next_instance_id = 5
    controllers._connect(0)

    play_frames([_joy(pygame.JOYDEVICEREMOVED, instance_id=5)])

    assert controllers.get_count() == 1
    assert controllers.get_axis(0, 1) == 0.0
    assert controllers.get_button(0, 0) is False
    assert controllers.get_hat(0, 0) == (0, 0)
    assert controllers.get_ball(0, 0) == (0, 0)
    assert [
        controllers.get_num_axes(0),
        controllers.get_num_buttons(0),
        controllers.get_num_hats(0),
        controllers.get_num_balls(0),
    ] == [0, 0, 0, 0]


def test_a_controller_gone_before_it_opens_is_skipped(monkeypatch):
    def vanished(device_index):
        raise pygame.error("Invalid joystick device number")

    monkeypatch.setattr("play.io.controllers._Controller", vanished)
    monkeypatch.setattr(controllers, "_controllers", [])
    frames = []
    play.repeat_forever(lambda: frames.append(1))

    play_frames([_joy(pygame.JOYDEVICEADDED, device_index=3)])

    assert controllers.get_count() == 0
    assert len(frames) > 3


def test_every_index_below_the_count_is_a_controller_also_after_an_unplug(
    fake_joysticks,
):
    for instance_id in (5, 6):
        fake_joysticks.next_instance_id = instance_id
        controllers._connect(instance_id - 5)

    play_frames([_joy(pygame.JOYDEVICEREMOVED, instance_id=5)])

    axes = [controllers.get_axis(index, 0) for index in range(controllers.get_count())]
    assert axes == [0.0, 0.75]
    assert controllers.get_all_controllers()[1] is controllers.get_controller(1)


def test_a_controller_announced_again_at_start_up_is_counted_once(fake_joysticks):
    fake_joysticks.next_instance_id = 5
    controllers._connect(0)

    play_frames([_joy(pygame.JOYDEVICEADDED, device_index=0)])

    assert controllers.get_count() == 1


def test_an_unplugged_controller_answers_every_joystick_method(fake_joysticks):
    fake_joysticks.next_instance_id = 5
    controllers._connect(0)

    play_frames([_joy(pygame.JOYDEVICEREMOVED, instance_id=5)])

    stand_in = controllers.get_all_controllers()[0]
    for name in dir(pygame.joystick.JoystickType):
        if not name.startswith("_"):
            assert hasattr(stand_in, name), name
    assert stand_in.get_name() == ""
    assert stand_in.rumble(0.5, 0.5, 100) is False


def test_a_button_combination_fires_when_its_last_button_goes_down():
    fired = []
    controllers.when_button_pressed(0, [1, 2])(lambda button: fired.append(button))

    play_frames(
        [_joy(pygame.JOYBUTTONDOWN, instance_id=0, button=1)],
        [_joy(pygame.JOYBUTTONDOWN, instance_id=0, button=2)],
        [_joy(pygame.JOYBUTTONDOWN, instance_id=0, button=3)],
    )

    assert fired == [{1, 2}]
