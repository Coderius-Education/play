"""Tests for screen properties."""

import pytest
import sys

sys.path.insert(0, ".")


def test_screen_width_getter():
    """Test getting screen width."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.width)
        play.stop_program()

    play.start_program()

    assert result[0] == 800  # default width


def test_screen_height_getter():
    """Test getting screen height."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.height)
        play.stop_program()

    play.start_program()

    assert result[0] == 600  # default height


def test_screen_top():
    """Test screen top boundary."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.top)
        play.stop_program()

    play.start_program()

    assert result[0] == 300  # half of 600


def test_screen_bottom():
    """Test screen bottom boundary."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.bottom)
        play.stop_program()

    play.start_program()

    assert result[0] == -300  # negative half of 600


def test_screen_left():
    """Test screen left boundary."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.left)
        play.stop_program()

    play.start_program()

    assert result[0] == -400  # negative half of 800


def test_screen_right():
    """Test screen right boundary."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.right)
        play.stop_program()

    play.start_program()

    assert result[0] == 400  # half of 800


def test_screen_caption_getter():
    """Test getting screen caption."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.caption)
        play.stop_program()

    play.start_program()

    assert result[0] == "coderius-play"  # default caption


def test_screen_caption_setter():
    """Test setting screen caption."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        play.screen.caption = "My Game"
        result.append(play.screen.caption)
        play.stop_program()

    play.start_program()

    assert result[0] == "My Game"


def test_screen_size():
    """Test screen size property."""
    import play

    box = play.new_box()
    box.start_physics()

    result = []

    @play.when_program_starts
    def check():
        result.append(play.screen.size)
        play.stop_program()

    play.start_program()

    assert result[0] == (800, 600)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
