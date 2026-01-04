"""Tests for wall side parameter in when_touching_wall and when_stopped_touching_wall."""

import pytest
import sys

sys.path.insert(0, ".")


def test_wallside_enum_exists():
    """Test that WallSide enum is accessible from play module."""
    import play

    assert hasattr(play, "WallSide")
    assert hasattr(play.WallSide, "TOP")
    assert hasattr(play.WallSide, "BOTTOM")
    assert hasattr(play.WallSide, "LEFT")
    assert hasattr(play.WallSide, "RIGHT")


def test_wallside_enum_values():
    """Test WallSide enum values."""
    import play

    assert play.WallSide.TOP.value == "top"
    assert play.WallSide.BOTTOM.value == "bottom"
    assert play.WallSide.LEFT.value == "left"
    assert play.WallSide.RIGHT.value == "right"


def test_walls_have_wall_side_attribute():
    """Test that walls have wall_side attribute."""
    import play
    from play.globals import globals_list

    # There should be 4 walls
    assert len(globals_list.walls) == 4

    # Each wall should have a wall_side attribute
    wall_sides = [wall.wall_side for wall in globals_list.walls]
    assert play.WallSide.TOP in wall_sides
    assert play.WallSide.BOTTOM in wall_sides
    assert play.WallSide.LEFT in wall_sides
    assert play.WallSide.RIGHT in wall_sides


def test_when_touching_wall_no_filter():
    """Test when_touching_wall without wall filter registers for all walls."""
    import play
    from play.callback import callback_manager, CallbackType

    box = play.new_box(color="red", x=0, y=0, width=50, height=50)

    callback_called = []

    @box.when_touching_wall
    def on_wall():
        callback_called.append(True)

    # Verify callbacks were registered for all 4 walls
    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_TOUCHING_WALL], id(box))
    )
    assert len(callbacks) == 4


def test_when_touching_wall_with_single_wall_filter():
    """Test when_touching_wall with single wall filter."""
    import play
    from play.callback import callback_manager, CallbackType

    box = play.new_box(color="blue", x=0, y=0, width=50, height=50)

    callback_called = []

    @box.when_touching_wall(wall=play.WallSide.LEFT)
    def on_left_wall():
        callback_called.append(True)

    # Verify callback was registered only for LEFT wall
    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_TOUCHING_WALL], id(box))
    )
    assert len(callbacks) == 1

    # Verify the wall_side is LEFT
    wrapper, wall_side = callbacks[0]
    assert wall_side == play.WallSide.LEFT


def test_when_touching_wall_with_multiple_wall_filter():
    """Test when_touching_wall with multiple walls filter."""
    import play
    from play.callback import callback_manager, CallbackType

    box = play.new_box(color="green", x=0, y=0, width=50, height=50)

    callback_called = []

    @box.when_touching_wall(wall=[play.WallSide.LEFT, play.WallSide.RIGHT])
    def on_side_walls():
        callback_called.append(True)

    # Verify callbacks were registered for LEFT and RIGHT walls only
    callbacks = list(
        callback_manager.get_callback([CallbackType.WHEN_TOUCHING_WALL], id(box))
    )
    assert len(callbacks) == 2

    wall_sides = [cb[1] for cb in callbacks]
    assert play.WallSide.LEFT in wall_sides
    assert play.WallSide.RIGHT in wall_sides
    assert play.WallSide.TOP not in wall_sides
    assert play.WallSide.BOTTOM not in wall_sides


def test_when_stopped_touching_wall_with_filter():
    """Test when_stopped_touching_wall with wall filter."""
    import play
    from play.callback import callback_manager, CallbackType

    box = play.new_box(color="yellow", x=0, y=0, width=50, height=50)

    callback_called = []

    @box.when_stopped_touching_wall(wall=play.WallSide.TOP)
    def on_stopped_top():
        callback_called.append(True)

    # Verify callback was registered for TOP wall
    callbacks = list(
        callback_manager.get_callback(
            [CallbackType.WHEN_STOPPED_TOUCHING_WALL], id(box)
        )
    )
    assert len(callbacks) == 1

    wrapper, wall_side = callbacks[0]
    assert wall_side == play.WallSide.TOP


def test_when_touching_wall_callback_receives_wall_parameter():
    """Test that callback can optionally receive wall parameter."""
    import play

    box = play.new_box(color="purple", x=0, y=0, width=50, height=50)

    # This should work without errors - callback takes wall parameter
    @box.when_touching_wall
    def on_wall_with_param(wall):
        pass

    # This should also work - callback takes no parameter
    @box.when_touching_wall
    def on_wall_no_param():
        pass


def test_get_touching_walls_for_non_physics_sprite():
    """Test get_touching_walls returns correct walls for non-physics sprites."""
    import play

    # Create a box at the left edge
    box = play.new_box(
        color="cyan", x=-play.screen.width / 2, y=0, width=50, height=50
    )

    touching = box.get_touching_walls()
    assert play.WallSide.LEFT in touching

    # Move to center - should not touch any walls
    box.x = 0
    box.y = 0
    touching = box.get_touching_walls()
    assert len(touching) == 0

    # Move to top right corner
    box.x = play.screen.width / 2
    box.y = play.screen.height / 2
    touching = box.get_touching_walls()
    assert play.WallSide.RIGHT in touching
    assert play.WallSide.TOP in touching
