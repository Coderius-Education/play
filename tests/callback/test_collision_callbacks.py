"""Tests for collision callback system."""

import pytest
import sys

sys.path.insert(0, ".")


def test_collision_registry_exists():
    """Test that collision_registry exists."""
    import play
    from play.callback.collision_callbacks import collision_registry

    result = []

    @play.when_program_starts
    def check():
        result.append(collision_registry is not None)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_wall_side_enum():
    """Test WallSide enum has all sides."""
    import play
    from play.callback.collision_callbacks import WallSide

    result = []

    @play.when_program_starts
    def check():
        result.append(hasattr(WallSide, "TOP"))
        result.append(hasattr(WallSide, "BOTTOM"))
        result.append(hasattr(WallSide, "LEFT"))
        result.append(hasattr(WallSide, "RIGHT"))
        play.stop_program()

    play.start_program()

    assert all(result)


def test_collision_type_enum():
    """Test CollisionType enum exists."""
    import play
    from play.callback.collision_callbacks import CollisionType

    result = []

    @play.when_program_starts
    def check():
        result.append(hasattr(CollisionType, "SPRITE"))
        result.append(hasattr(CollisionType, "WALL"))
        play.stop_program()

    play.start_program()

    assert all(result)


def test_when_touching_callback_fires():
    """Test when_touching callback fires on collision."""
    import play

    box1 = play.new_box(x=-50)
    box1.start_physics(x_speed=200, obeys_gravity=False)

    box2 = play.new_box(x=50)
    box2.start_physics(can_move=False)

    collision_count = [0]
    frame_count = [0]

    @box1.when_touching(box2)
    def on_collision():
        collision_count[0] += 1

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 60:
            play.stop_program()

    play.start_program()

    assert collision_count[0] > 0


def test_when_stopped_touching_callback_fires():
    """Test when_stopped_touching callback fires after collision ends."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics(x_speed=300, obeys_gravity=False, bounciness=0.8)

    box2 = play.new_box(x=0)
    box2.start_physics(can_move=False)

    stopped_touching = [False]
    frame_count = [0]

    @box1.when_stopped_touching(box2)
    def on_stop():
        stopped_touching[0] = True

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 120 or stopped_touching[0]:
            play.stop_program()

    play.start_program()

    assert stopped_touching[0] is True


def test_when_touching_wall_callback():
    """Test when_touching_wall callback fires."""
    import play

    # Place box near right wall and move it right
    box = play.new_box(x=350)
    box.start_physics(x_speed=200, obeys_gravity=False)

    touched_wall = [False]
    frame_count = [0]

    @box.when_touching_wall()
    def on_wall():
        touched_wall[0] = True

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 30 or touched_wall[0]:
            play.stop_program()

    play.start_program()

    assert touched_wall[0] is True


def test_when_touching_wall_specific_side():
    """Test when_touching_wall with specific wall side."""
    import play
    from play.callback.collision_callbacks import WallSide

    # Place box near right wall
    box = play.new_box(x=350)
    box.start_physics(x_speed=200, obeys_gravity=False)

    touched_right = [False]
    frame_count = [0]

    @box.when_touching_wall(wall=WallSide.RIGHT)
    def on_right_wall():
        touched_right[0] = True

    @play.repeat_forever
    def check():
        frame_count[0] += 1
        if frame_count[0] > 30 or touched_right[0]:
            play.stop_program()

    play.start_program()

    assert touched_right[0] is True


def test_collision_registry_register():
    """Test that collision registry can register collisions."""
    import play
    from play.callback.collision_callbacks import collision_registry

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    result = []

    @play.when_program_starts
    def check():
        # Registry should have callbacks dict
        result.append(hasattr(collision_registry, "callbacks"))
        result.append(hasattr(collision_registry, "shape_registry"))
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
