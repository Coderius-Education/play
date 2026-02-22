"""Tests for sprite update methods: _update_sprite_collisions and _update_wall_collisions."""


def test_update_sprite_collisions_touching(monkeypatch):
    """Test _update_sprite_collisions updates _touching_callback when sprites overlap."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=0, y=0, width=50, height=50)

    # Decorator automatically hooks into callback_manager
    @sprite1.when_touching(sprite2)
    async def touching():
        pass

    # Mock physics to None so the physics guard is bypassed,
    # and mock is_touching to control collision detection directly
    # (mirrors the pattern used in wall collision tests).
    monkeypatch.setattr(sprite1, "physics", None)
    monkeypatch.setattr(sprite2, "physics", None)
    monkeypatch.setattr(sprite1, "is_touching", lambda s: True)

    assert id(sprite2) not in sprite1.events._touching_callback

    result = []

    @play.when_program_starts
    def check():
        sprite1.events._update_sprite_collisions()
        result.append(id(sprite2) in sprite1.events._touching_callback)
        play.stop_program()

    play.start_program()

    assert result[0] is True


def test_update_sprite_collisions_stopped_touching(monkeypatch):
    """Test _update_sprite_collisions updates _stopped_callback when sprites separate."""
    import play

    sprite1 = play.new_box(x=0, y=0, width=50, height=50)
    sprite2 = play.new_box(x=0, y=0, width=50, height=50)

    @sprite1.when_stopped_touching(sprite2)
    async def stopped():
        pass

    is_touching_now = [True]

    monkeypatch.setattr(sprite1, "physics", None)
    monkeypatch.setattr(sprite2, "physics", None)
    monkeypatch.setattr(sprite1, "is_touching", lambda s: is_touching_now[0])

    result = []

    @play.when_program_starts
    def check():
        # First simulate that they are touching
        sprite1.events._update_sprite_collisions()
        result.append(id(sprite2) in sprite1.events._touching_callback)

        # Now simulate them separating
        is_touching_now[0] = False
        sprite1.events._update_sprite_collisions()

        result.append(id(sprite2) not in sprite1.events._touching_callback)
        result.append(id(sprite2) in sprite1.events._stopped_callback)
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
