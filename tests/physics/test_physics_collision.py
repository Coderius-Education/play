import pygame
import pytest

import play
from play.physics import physics_space


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_static_body_does_not_sleep():
    """Bodies should never sleep — sleeping disables collision detection."""
    ramp = play.new_box(y=-100, width=500, height=20, angle=15)

    # Step the simulation long enough that sleep would have kicked in
    # with the old sleep_time_threshold=0.5
    for _ in range(100):
        physics_space.step(1 / 60)

    assert not ramp.physics._pymunk_body.is_sleeping


def test_angled_platform_collision():
    """A falling box must collide with an angled platform, not pass through."""
    ramp = play.new_box(y=-100, width=500, height=20, angle=15)
    ramp.start_physics(can_move=False)

    block = play.new_box(x=0, y=100, width=40, height=40, color="red")
    block.start_physics(obeys_gravity=True)

    # Run enough physics steps for the block to fall onto the ramp
    for _ in range(300):
        physics_space.step(1 / 60)

    # The block should have landed on the ramp, not fallen through
    assert block.physics._pymunk_body.position.y > ramp.physics._pymunk_body.position.y


def test_sensor_via_start_physics():
    """A sensor shape detects collisions but does not block movement."""
    platform = play.new_box(y=-50, width=200, height=20)
    platform.start_physics(can_move=False, sensor=True)

    assert platform.physics.sensor is True
    assert platform.physics._pymunk_shape.sensor is True


def test_sensor_property_setter():
    """The sensor property can be toggled at runtime."""
    box = play.new_box()
    box.start_physics(can_move=False)

    assert box.physics.sensor is False
    box.physics.sensor = True
    assert box.physics.sensor is True
    assert box.physics._pymunk_shape.sensor is True


def test_sensor_does_not_block():
    """A falling block should pass through a sensor platform."""
    platform = play.new_box(y=-50, width=200, height=20)
    platform.start_physics(can_move=False, sensor=True)

    block = play.new_box(y=0, width=20, height=20)
    block.start_physics(obeys_gravity=True)

    # Step until the block has fallen past the platform
    passed_through = False
    for _ in range(120):
        physics_space.step(1 / 60)
        if (
            block.physics._pymunk_body.position.y
            < platform.physics._pymunk_body.position.y
        ):
            passed_through = True
            break

    assert passed_through, "block should fall through a sensor platform"


def test_sensor_preserved_by_clone():
    """Cloning a physics object should preserve the sensor flag."""
    box = play.new_box()
    box.start_physics(can_move=False, sensor=True)

    other = play.new_box(x=50)
    cloned = box.physics.clone(other)

    assert cloned.sensor is True


def test_sensor_setter_survives_remake():
    """Sensor flag set via property must persist when _make_pymunk() rebuilds the shape."""
    box = play.new_box()
    box.start_physics(can_move=False)
    box.physics.sensor = True
    box.physics.can_move = True  # triggers _make_pymunk()
    assert box.physics.sensor is True


def test_sleep_disabled_on_space():
    """The physics space should not have body sleeping enabled."""
    assert physics_space.sleep_time_threshold == float("inf")
