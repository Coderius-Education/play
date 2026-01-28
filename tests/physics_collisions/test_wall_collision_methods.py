"""Tests for is_touching_wall() and get_touching_walls() methods."""

import pytest
import sys

sys.path.insert(0, ".")


def test_is_touching_wall_false():
    """Test is_touching_wall() returns False when not touching wall."""
    import play

    box = play.new_box(x=0, y=0)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_touching_wall())
        play.stop_program()

    play.start_program()

    assert result[0] is False


def test_is_touching_wall_right():
    """Test is_touching_wall() returns True when touching right wall."""
    import play

    # Place box at right edge
    box = play.new_box(x=380, y=0, width=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_touching_wall())
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_is_touching_wall_left():
    """Test is_touching_wall() returns True when touching left wall."""
    import play

    # Place box at left edge
    box = play.new_box(x=-380, y=0, width=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_touching_wall())
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_is_touching_wall_top():
    """Test is_touching_wall() returns True when touching top wall."""
    import play

    # Place box at top edge
    box = play.new_box(x=0, y=280, height=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_touching_wall())
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_is_touching_wall_bottom():
    """Test is_touching_wall() returns True when touching bottom wall."""
    import play

    # Place box at bottom edge
    box = play.new_box(x=0, y=-280, height=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.is_touching_wall())
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_get_touching_walls_empty():
    """Test get_touching_walls() returns empty list when not touching."""
    import play

    box = play.new_box(x=0, y=0)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(box.get_touching_walls())
        play.stop_program()

    play.start_program()

    assert result[0] == []


def test_get_touching_walls_right():
    """Test get_touching_walls() includes RIGHT when touching right wall."""
    import play
    from play.callback.collision_callbacks import WallSide

    # Place box at right edge
    box = play.new_box(x=380, y=0, width=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        walls = box.get_touching_walls()
        result.append(walls)
        play.stop_program()

    play.start_program()

    assert WallSide.RIGHT in result[0]


def test_get_touching_walls_multiple():
    """Test get_touching_walls() can return multiple walls (corner)."""
    import play
    from play.callback.collision_callbacks import WallSide

    # Place box in top-right corner
    box = play.new_box(x=380, y=280, width=50, height=50)
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        walls = box.get_touching_walls()
        result.append(walls)
        play.stop_program()

    play.start_program()

    assert len(result[0]) >= 2
    assert WallSide.RIGHT in result[0]
    assert WallSide.TOP in result[0]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
