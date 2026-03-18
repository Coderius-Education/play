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


@pytest.mark.parametrize(
    "make_sprite",
    [
        pytest.param(lambda: play.new_box(width=100, height=10, angle=45), id="box"),
        pytest.param(lambda: play.new_circle(radius=50, angle=45), id="circle"),
        pytest.param(
            lambda: play.new_image(
                image="tests/objects_attributes/yellow.jpg", angle=45
            ),
            id="image",
        ),
    ],
)
def test_visual_angle_matches_physics_angle(make_sprite, monkeypatch):
    """The rendered sprite must be rotated in the same direction as the physics body.

    Regression test: the visual angle was previously negated, making the rendered
    ramp tilt the opposite way from its collision shape.
    """
    captured_angles = []
    original_rotate = pygame.transform.rotate

    def spy_rotate(surface, angle):
        captured_angles.append(angle)
        return original_rotate(surface, angle)

    monkeypatch.setattr(pygame.transform, "rotate", spy_rotate)

    sprite = make_sprite()
    # Force the rendering path — update() skips work when _should_recompute is False.
    captured_angles.clear()
    sprite._should_recompute = True
    sprite.update()

    assert (
        len(captured_angles) == 1
    ), f"expected exactly one rotate call, got {len(captured_angles)}"
    assert captured_angles[0] == pytest.approx(
        45.0
    ), f"visual angle should be +45° (not negated), got {captured_angles[0]}"


def test_sleep_disabled_on_space():
    """The physics space should not have body sleeping enabled."""
    assert physics_space.sleep_time_threshold == float("inf")
