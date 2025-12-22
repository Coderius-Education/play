"""Tests for sprite methods like distance_to, etc."""

import pytest
import sys
import math

sys.path.insert(0, ".")


def test_sprite_distance_to_coordinates():
    """Test distance_to method with x, y coordinates."""
    import play

    sprite = play.new_box(x=0, y=0)
    distance = sprite.distance_to(3, 4)

    assert abs(distance - 5.0) < 0.1  # 3-4-5 triangle


def test_sprite_distance_to_sprite():
    """Test distance_to method with another sprite."""
    import play

    sprite1 = play.new_box(x=0, y=0)
    sprite2 = play.new_circle(x=3, y=4)

    distance = sprite1.distance_to(sprite2)

    assert abs(distance - 5.0) < 0.1  # 3-4-5 triangle


def test_sprite_distance_to_same_position():
    """Test distance_to when sprites are at same position."""
    import play

    sprite1 = play.new_box(x=100, y=100)
    sprite2 = play.new_circle(x=100, y=100)

    distance = sprite1.distance_to(sprite2)

    assert abs(distance) < 0.1


def test_sprite_hide_show():
    """Test hide and show methods."""
    import play

    sprite = play.new_box()

    assert sprite.is_hidden == False

    sprite.hide()
    assert sprite.is_hidden == True

    sprite.show()
    assert sprite.is_hidden == False


def test_sprite_remove():
    """Test remove method."""
    import play

    sprite = play.new_box()

    # Verify sprite is in the group
    from play.globals import globals_list

    assert sprite in globals_list.sprites_group

    sprite.remove()

    # Verify sprite is no longer in the group
    assert sprite not in globals_list.sprites_group


def test_sprite_position_properties():
    """Test sprite position properties (left, right, top, bottom)."""
    import play

    sprite = play.new_box(x=0, y=0, width=100, height=100)

    # Test getters
    assert abs(sprite.left - (-50)) < 1
    assert abs(sprite.right - 50) < 1
    assert abs(sprite.bottom - (-50)) < 1
    assert abs(sprite.top - 50) < 1


def test_sprite_position_setters():
    """Test setting sprite position properties."""
    import play

    sprite = play.new_box(x=0, y=0, width=100, height=100)

    # Test setters
    sprite.left = 0
    assert abs(sprite.x - 50) < 1

    sprite.right = 0
    assert abs(sprite.x - (-50)) < 1

    sprite.bottom = 0
    assert abs(sprite.y - 50) < 1

    sprite.top = 0
    assert abs(sprite.y - (-50)) < 1


def test_sprite_width_height():
    """Test sprite width and height properties."""
    import play

    sprite = play.new_box(width=100, height=200)

    assert sprite.width > 0
    assert sprite.height > 0


def test_box_clone():
    """Test cloning a box sprite."""
    import play

    box1 = play.new_box(x=100, y=200, width=150, height=200, color="red", angle=45)

    box2 = box1.clone()

    assert box2.x == box1.x
    assert box2.y == box1.y
    assert box2.width == box1.width
    assert box2.height == box1.height
    assert box2.color == box1.color
    assert box2.angle == box1.angle

    # Verify they are different objects
    assert box1 is not box2


def test_circle_clone():
    """Test cloning a circle sprite."""
    import play

    circle1 = play.new_circle(x=100, y=200, radius=50, color="blue", angle=30)

    circle2 = circle1.clone()

    assert circle2.x == circle1.x
    assert circle2.y == circle1.y
    assert circle2.radius == circle1.radius
    assert circle2.color == circle1.color
    assert circle2.angle == circle1.angle

    # Verify they are different objects
    assert circle1 is not circle2


def test_sprite_is_touching_sprite():
    """Test is_touching method between sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=0, y=0, width=50, height=50)

    # Sprites at same position should be touching
    assert sprite1.is_touching(sprite2) == True


def test_sprite_not_touching():
    """Test is_touching when sprites are far apart."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=1000, y=1000, width=50, height=50)

    # Sprites far apart should not be touching
    assert sprite1.is_touching(sprite2) == False


def test_sprite_transparency_setter():
    """Test setting sprite transparency."""
    import play

    sprite = play.new_box()

    sprite.transparency = 0.5
    assert sprite.transparency == 0.5

    sprite.transparency = 1.0
    assert sprite.transparency == 1.0


def test_sprite_transparency_invalid():
    """Test that invalid transparency raises ValueError."""
    import play

    sprite = play.new_box()

    with pytest.raises(ValueError):
        sprite.transparency = "not a number"
