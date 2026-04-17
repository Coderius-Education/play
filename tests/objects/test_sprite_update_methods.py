"""Tests for sprite update methods: _update_wall_collisions."""


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
    assert collision_key not in sprite.events._touching_callback

    result = []

    @play.when_program_starts
    def check():
        sprite.events._update_wall_collisions()
        result.append(collision_key in sprite.events._touching_callback)
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
        sprite.events._update_wall_collisions()
        result.append(collision_key in sprite.events._touching_callback)

        # Change to not touching walls
        touching_walls.clear()

        sprite.events._update_wall_collisions()

        result.append(collision_key not in sprite.events._touching_callback)
        result.append(collision_key in sprite.events._stopped_callback)

        play.stop_program()

    play.start_program()

    assert result[0] is True
    assert result[1] is True
    assert result[2] is True
