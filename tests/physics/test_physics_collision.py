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


def test_visual_angle_matches_physics_angle():
    """The rendered sprite must be rotated in the same direction as the physics body.

    Regression test: the visual angle was previously negated, making the rendered
    ramp tilt the opposite way from its collision shape.
    """
    import math
    import pygame

    # A thin, wide box at 45° makes the direction of tilt easy to verify.
    box = play.new_box(width=100, height=10, angle=45)
    box._should_recompute = True
    box.update()

    img = box.image
    cx, cy = img.get_width() // 2, img.get_height() // 2

    # With correct +45° CCW rotation the bar runs from lower-left to upper-right,
    # so a point offset (+20, -20) from centre (upper-right) should be opaque.
    upper_right = img.get_at((cx + 20, cy - 20))
    # And a point at (+20, +20) from centre (lower-right) should be transparent.
    lower_right = img.get_at((cx + 20, cy + 20))

    assert (
        upper_right.a > 0
    ), "upper-right should be opaque (bar runs lower-left → upper-right)"
    assert lower_right.a == 0, "lower-right should be transparent"


def test_sleep_disabled_on_space():
    """The physics space should not have body sleeping enabled."""
    assert physics_space.sleep_time_threshold == float("inf")
