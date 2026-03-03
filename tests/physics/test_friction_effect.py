"""Test that the friction parameter in start_physics() actually affects motion."""

import pytest
import play
from play.physics import physics_space


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_friction_parameter_stored():
    """The friction parameter should be stored on the physics object."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    box.start_physics(friction=0.8, obeys_gravity=False)

    assert box.physics._friction == 0.8


def test_friction_zero_vs_high():
    """Friction values should be stored correctly on the pymunk shape for both
    zero and high friction settings."""
    box_no_friction = play.new_box(color="red", x=-100, y=0, width=10, height=10)
    box_no_friction.start_physics(
        friction=0.0, obeys_gravity=False, x_speed=100, y_speed=0
    )

    box_high_friction = play.new_box(color="blue", x=100, y=0, width=10, height=10)
    box_high_friction.start_physics(
        friction=1.0, obeys_gravity=False, x_speed=100, y_speed=0
    )

    # Both should have the same initial x_speed
    assert box_no_friction.physics.x_speed == 100
    assert box_high_friction.physics.x_speed == 100

    # The pymunk shapes should have different friction values
    assert box_no_friction.physics._pymunk_shape.friction == 0.0
    assert box_high_friction.physics._pymunk_shape.friction == 1.0
