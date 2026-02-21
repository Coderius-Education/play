"""Tests for sprite update methods: _update_sprite_collisions and _update_wall_collisions."""

import sys

sys.path.insert(0, ".")


def test_update_sprite_collisions_touching():
    """Test manual collision checks with other sprites."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=0, y=0, width=50, height=50)

    # Decorator automatically hooks into callback_manager
    @sprite1.when_touching(sprite2)
    async def touching():
        pass

    assert id(sprite2) not in sprite1._touching_callback

    result = []

    @play.when_program_starts
    def check():
        # We manually trigger the internal logic which happens every frame in update()
        sprite1._update_sprite_collisions()
        result.append(id(sprite2) in sprite1._touching_callback)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_update_sprite_collisions_stopped_touching():
    """Test manual collision checks when stopping touching."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=0, y=0, width=50, height=50)

    @sprite1.when_stopped_touching(sprite2)
    async def stopped():
        pass

    result = []

    @play.when_program_starts
    def check():
        # First we simulate that they are touching by manually triggering update
        sprite1._update_sprite_collisions()

        # They were touching, so it's registered in _touching_callback
        result.append(id(sprite2) in sprite1._touching_callback)

        # Move them apart
        sprite2.x = 1000
        sprite2.y = 1000

        # Call it again
        sprite1._update_sprite_collisions()

        # It should have noted they stopped touching
        result.append(id(sprite2) not in sprite1._touching_callback)
        result.append(id(sprite2) in sprite1._stopped_callback)
        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True
    assert result[2] is True


def test_update_wall_collisions_touching(monkeypatch):
    """Test manual collision checks with walls."""
    import play
    from play.callback.collision_callbacks import WallSide, CollisionType

    sprite = play.new_box(x=0, y=0, width=50, height=50)

    @sprite.when_touching_wall
    async def touch_wall():
        pass

    # Mock get_touching_walls
    def mock_get_touching_walls():
        return [WallSide.TOP]

    monkeypatch.setattr(sprite, "get_touching_walls", mock_get_touching_walls)

    collision_key = (CollisionType.WALL, WallSide.TOP)
    assert collision_key not in sprite._touching_callback

    result = []

    @play.when_program_starts
    def check():
        sprite._update_wall_collisions()
        result.append(collision_key in sprite._touching_callback)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_update_wall_collisions_stopped_touching(monkeypatch):
    """Test manual collision checks when stopped touching walls."""
    import play
    from play.callback.collision_callbacks import WallSide, CollisionType

    sprite = play.new_box(x=0, y=0, width=50, height=50)

    @sprite.when_stopped_touching_wall
    async def stop_touch_wall():
        pass

    touching_walls = [WallSide.BOTTOM]

    def mock_get_touching_walls():
        return touching_walls

    monkeypatch.setattr(sprite, "get_touching_walls", mock_get_touching_walls)

    collision_key = (CollisionType.WALL, WallSide.BOTTOM)
    result = []

    @play.when_program_starts
    def check():
        sprite._update_wall_collisions()
        result.append(collision_key in sprite._touching_callback)

        # Change to not touching walls
        touching_walls.clear()

        sprite._update_wall_collisions()

        result.append(collision_key not in sprite._touching_callback)
        result.append(collision_key in sprite._stopped_callback)

        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True
    assert result[2] is True
