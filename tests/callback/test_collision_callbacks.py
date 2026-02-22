"""Tests for collision callback system."""

import pytest


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


def test_duplicate_when_touching_raises_error():
    """Test that registering two when_touching callbacks for same sprite pair raises ValueError."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    @box1.when_touching(box2)
    def first_callback():
        pass

    with pytest.raises(ValueError) as exc_info:

        @box1.when_touching(box2)
        def second_callback():
            pass

    assert "when_touching" in str(exc_info.value)
    assert "already" in str(exc_info.value).lower()


def test_duplicate_when_stopped_touching_raises_error():
    """Test that registering two when_stopped_touching callbacks for same sprite pair raises ValueError."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    @box1.when_stopped_touching(box2)
    def first_callback():
        pass

    with pytest.raises(ValueError) as exc_info:

        @box1.when_stopped_touching(box2)
        def second_callback():
            pass

    assert "when_stopped_touching" in str(exc_info.value)
    assert "already" in str(exc_info.value).lower()


def test_duplicate_callback_error_message_is_user_friendly():
    """Test that duplicate callback error message is clear for beginners."""
    import play

    circle = play.new_circle(x=-50)
    circle.start_physics()

    box = play.new_box(x=50)
    box.start_physics()

    @circle.when_touching(box)
    def first():
        pass

    with pytest.raises(ValueError) as exc_info:

        @circle.when_touching(box)
        def second():
            pass

    error_message = str(exc_info.value)
    # Check that message explains the issue and solution
    assert (
        "two sprites" in error_message.lower()
        or "these two sprites" in error_message.lower()
    )
    assert "single function" in error_message.lower()


def test_collision_attributes_preserved_after_can_move_change():
    """Test that collision attributes survive when can_move recreates the physics shape."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    @box1.when_touching(box2)
    def on_touch():
        pass

    old_collision_type = box1.physics._pymunk_shape.collision_type
    old_collision_id = box1.physics._pymunk_shape.collision_id

    # Changing can_move recreates the shape
    box1.physics.can_move = False

    assert box1.physics._pymunk_shape.collision_type == old_collision_type
    assert box1.physics._pymunk_shape.collision_id == old_collision_id


def test_collision_attributes_preserved_after_stable_change():
    """Test that collision attributes survive when stable recreates the physics shape."""
    import play

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    @box1.when_touching(box2)
    def on_touch():
        pass

    old_collision_type = box1.physics._pymunk_shape.collision_type
    old_collision_id = box1.physics._pymunk_shape.collision_id

    # Changing stable recreates the shape
    box1.physics.stable = True

    assert box1.physics._pymunk_shape.collision_type == old_collision_type
    assert box1.physics._pymunk_shape.collision_id == old_collision_id


def test_collision_registry_valid_after_can_move_change():
    """Test that the collision registry can still find the callback after can_move change."""
    import play
    from play.callback.collision_callbacks import collision_registry

    box1 = play.new_box(x=-100)
    box1.start_physics()

    box2 = play.new_box(x=100)
    box2.start_physics()

    @box1.when_touching(box2)
    def on_touch():
        pass

    # Changing can_move recreates the shape
    box1.physics.can_move = False

    # The registry should still map the collision_type to the sprite
    ct = box1.physics._pymunk_shape.collision_type
    assert ct in collision_registry.shape_registry
    assert ct in collision_registry.callbacks[True]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
