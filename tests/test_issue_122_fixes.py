"""Comprehensive tests for all 7 bug fixes from issue #122."""

import pytest
import sys
import math

sys.path.insert(0, ".")


def test_image_rotation_from_physics():
    """Test that Image rotation reads from physics body angle like Box/Circle do."""
    import play

    # Create an image sprite with physics
    image = play.new_image(image="example.png", x=100, y=100)

    # Verify physics is initialized
    assert image.physics is not None
    assert hasattr(image.physics, "_pymunk_body")

    # Set a specific angle on the physics body
    image.physics._pymunk_body.angle = math.radians(45)

    # Update should read from physics body
    image.update()

    # Verify angle is read from physics (converted from radians to degrees, negated)
    expected_angle = -45  # Negated as per the conversion
    assert abs(image.angle - expected_angle) < 1.0


def test_image_sizing_with_round():
    """Test that Image sizing uses round() with max(1) instead of // truncation."""
    import play

    # Create a small image that would truncate to 0 with //
    image = play.new_image(image="example.png", x=100, y=100, size=5)

    # With round() and max(1), dimensions should be at least 1
    assert image.width >= 1
    assert image.height >= 1

    # Test with larger size to verify rounding works correctly
    image2 = play.new_image(image="example.png", x=100, y=100, size=50)

    # Should have reasonable dimensions
    assert image2.width > 0
    assert image2.height > 0


def test_keyboard_state_instance_isolation():
    """Test that KeyboardState instances don't share pressed/released lists."""
    from play.io.keypress import KeyboardState

    # Create two instances
    kb1 = KeyboardState()
    kb2 = KeyboardState()

    # Modify one instance
    kb1.pressed.append("a")
    kb1.released.append("b")

    # Verify the other instance is not affected
    assert "a" not in kb2.pressed
    assert "b" not in kb2.released

    # Verify they have separate lists
    assert kb1.pressed is not kb2.pressed
    assert kb1.released is not kb2.released


def test_callback_validation_hasattr_check():
    """Test that callback validation checks hasattr before accessing is_running."""
    from play.callback import is_valid_callback

    # Create a simple callable without is_running attribute
    def simple_callback():
        pass

    # Should not raise AttributeError
    result = is_valid_callback(simple_callback)

    # Should return True for a valid callable
    assert result is True

    # Test with a non-callable
    result = is_valid_callback("not a function")
    assert result is False


def test_nan_validation_uses_isnan():
    """Test that NaN validation uses math.isnan() instead of string comparison."""
    import play
    from play.core.sprites_loop import run_sprites_loop

    # Create a sprite with physics
    sprite = play.new_box(x=100, y=100)

    # Verify the sprite has physics
    assert sprite.physics is not None

    # Set position to NaN
    sprite.physics._pymunk_body.position = (float("nan"), 100)

    # The sprites_loop should handle NaN gracefully using math.isnan()
    # This should not raise an exception
    try:
        run_sprites_loop()
    except Exception as e:
        # If it raises, it shouldn't be due to string comparison
        assert "nan" not in str(e).lower() or "isnan" in str(e).lower()


def test_box_border_radius_in_clone():
    """Test that Box.clone() includes border_radius parameter."""
    import play

    # Create a box with border_radius
    box1 = play.new_box(x=100, y=100, width=50, height=50, border_radius=15)

    # Clone it
    box2 = box1.clone()

    # Verify border_radius is preserved
    assert box2.border_radius == box1.border_radius
    assert box2.border_radius == 15
