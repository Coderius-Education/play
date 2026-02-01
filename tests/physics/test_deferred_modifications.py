"""Test that physics modifications are properly deferred during simulation."""

import pytest

num_frames = 0
max_frames = 100
modifications_applied = []


def test_deferred_physics_modifications_in_collision():
    """Test that physics modifications in collision callbacks are deferred until after physics steps."""
    import sys

    sys.path.insert(0, ".")
    import play

    global num_frames, modifications_applied
    num_frames = 0
    modifications_applied = []

    # Create two sprites that will collide
    sprite1 = play.new_box(x=-100, y=0, width=50, height=50, color="blue")
    sprite1.start_physics(x_speed=100, obeys_gravity=False)

    sprite2 = play.new_box(x=100, y=0, width=50, height=50, color="red")
    sprite2.start_physics(x_speed=0, obeys_gravity=False)

    collision_count = 0

    @sprite1.when_touching(sprite2)
    async def handle_collision():
        """This runs during physics simulation - modifications should be deferred."""
        nonlocal collision_count
        collision_count += 1

        # Record the current x_speed before modification
        old_speed = sprite1.physics.x_speed

        # Modify physics during collision callback (during physics simulation)
        sprite1.physics.x_speed = -50
        sprite1.physics.y_speed = 100

        # Record that we attempted modification
        modifications_applied.append(
            {
                "frame": num_frames,
                "old_speed": old_speed,
                "new_speed_requested": -50,
            }
        )

    @play.repeat_forever
    def check_frame():
        global num_frames
        num_frames += 1

        if num_frames >= max_frames:
            play.stop_program()

    play.start_program()

    # Verify that collision happened and modifications were made
    assert collision_count > 0, "Collision should have occurred"
    assert len(modifications_applied) > 0, "Physics modifications should have been attempted"

    # Verify that the sprite's speed was actually changed
    # (this confirms deferred modifications were applied)
    assert (
        sprite1.physics.x_speed == -50
    ), f"Expected x_speed to be -50, but got {sprite1.physics.x_speed}"
    assert (
        sprite1.physics.y_speed == 100
    ), f"Expected y_speed to be 100, but got {sprite1.physics.y_speed}"


def test_immediate_modifications_outside_simulation():
    """Test that physics modifications outside simulation are applied immediately."""
    import sys

    sys.path.insert(0, ".")
    import play

    sprite = play.new_box(x=0, y=0, width=50, height=50, color="green")
    sprite.start_physics(x_speed=50, y_speed=30, obeys_gravity=False)

    # Modify before starting the game loop (outside simulation)
    sprite.physics.x_speed = 100
    sprite.physics.y_speed = 200

    # Verify immediate application
    assert sprite.physics.x_speed == 100, "x_speed should be applied immediately"
    assert sprite.physics.y_speed == 200, "y_speed should be applied immediately"


def test_multiple_deferred_modifications():
    """Test that multiple deferred modifications are all applied in order."""
    import sys

    sys.path.insert(0, ".")
    import play

    global num_frames
    num_frames = 0

    sprite1 = play.new_box(x=-100, y=0, width=50, height=50, color="blue")
    sprite1.start_physics(x_speed=100, obeys_gravity=False)

    sprite2 = play.new_box(x=100, y=0, width=50, height=50, color="red")
    sprite2.start_physics(x_speed=0, obeys_gravity=False)

    modification_sequence = []

    @sprite1.when_touching(sprite2)
    async def handle_collision():
        """Apply multiple modifications in sequence."""
        # First modification
        sprite1.physics.x_speed = -50
        modification_sequence.append(("x_speed", -50))

        # Second modification
        sprite1.physics.y_speed = 100
        modification_sequence.append(("y_speed", 100))

        # Third modification
        sprite1.physics.bounciness = 0.8
        modification_sequence.append(("bounciness", 0.8))

        # Fourth modification
        sprite1.physics.mass = 5.0
        modification_sequence.append(("mass", 5.0))

    @play.repeat_forever
    def check_frame():
        global num_frames
        num_frames += 1

        if num_frames >= max_frames:
            play.stop_program()

    play.start_program()

    # Verify all modifications were applied in order
    assert len(modification_sequence) >= 4, "All modifications should have been recorded"
    assert sprite1.physics.x_speed == -50, "x_speed modification should be applied"
    assert sprite1.physics.y_speed == 100, "y_speed modification should be applied"
    assert (
        abs(sprite1.physics.bounciness - 0.8) < 0.01
    ), "bounciness modification should be applied"
    assert abs(sprite1.physics.mass - 5.0) < 0.01, "mass modification should be applied"


if __name__ == "__main__":
    test_deferred_physics_modifications_in_collision()
    test_immediate_modifications_outside_simulation()
    test_multiple_deferred_modifications()
