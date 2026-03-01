import pytest
import play
from play.callback.collision_callbacks import WallSide
import asyncio


def test_event_component_basics():
    sprite = play.new_circle(color="red", x=0, y=0, radius=10)

    # Test is_clicked property setup
    assert sprite.events.is_clicked is False
    sprite.events.is_clicked = True
    assert sprite.events.is_clicked is True
    assert sprite.is_clicked is True

    # Test collision dictionaries
    def dummy_cb():
        pass

    sprite.events.set_touching("test_key", dummy_cb)
    assert sprite.events.get_touching("test_key") == dummy_cb
    assert sprite.events.get_touching("wrong_key", "default") == "default"
    assert len(sprite.events.touching_callbacks()) == 1

    sprite.events.clear_touching("test_key")
    assert sprite.events.get_touching("test_key") is None

    sprite.events.set_stopped("stop_key", dummy_cb)
    assert len(sprite.events.stopped_callbacks()) == 1
    sprite.events.clear_all_stopped()
    assert len(sprite.events.stopped_callbacks()) == 0


def test_event_component_mouse_decorators():
    sprite = play.new_circle(color="red", x=0, y=0, radius=10)

    click_called = False
    click_with_sprite_args = None

    async def mock_click():
        nonlocal click_called
        click_called = True

    async def mock_click_with_sprite(sprite):
        nonlocal click_with_sprite_args
        click_with_sprite_args = sprite

    wrapper_click1 = sprite.when_clicked(mock_click)
    wrapper_click2 = sprite.when_clicked(mock_click_with_sprite, call_with_sprite=True)

    asyncio.run(wrapper_click1())
    assert click_called

    asyncio.run(wrapper_click2())
    assert click_with_sprite_args == sprite

    release_called = False
    release_with_sprite_args = None

    async def mock_release():
        nonlocal release_called
        release_called = True

    async def mock_release_with_sprite(sprite):
        nonlocal release_with_sprite_args
        release_with_sprite_args = sprite

    wrapper_release1 = sprite.when_click_released(mock_release)
    wrapper_release2 = sprite.when_click_released(
        mock_release_with_sprite, call_with_sprite=True
    )

    asyncio.run(wrapper_release1())
    assert release_called

    asyncio.run(wrapper_release2())
    assert release_with_sprite_args == sprite


def test_event_component_touching_decorators():
    sprite1 = play.new_box(color="red", x=0, y=0, width=10, height=10)
    sprite2 = play.new_box(color="blue", x=100, y=100, width=10, height=10)

    sprite1.start_physics()
    sprite2.start_physics()

    touching_called = False

    async def mock_touching():
        nonlocal touching_called
        touching_called = True

    wrapper_touch = sprite1.when_touching(sprite2)(mock_touching)

    asyncio.run(wrapper_touch())
    assert touching_called

    stopped_called = False

    async def mock_stopped():
        nonlocal stopped_called
        stopped_called = True

    wrapper_stop = sprite1.when_stopped_touching(sprite2)(mock_stopped)

    asyncio.run(wrapper_stop())
    assert stopped_called

    assert sprite1 in sprite2.events._dependent_sprites


def test_event_component_wall_decorators():
    sprite = play.new_circle(color="red", x=0, y=0, radius=10)
    sprite.start_physics()

    async def mock_touch_wall(wall):
        pass

    wrapper_wall = sprite.when_touching_wall(wall=WallSide.LEFT)(mock_touch_wall)

    async def mock_stop_wall(wall):
        pass

    wrapper_stop_wall = sprite.when_stopped_touching_wall(
        wall=[WallSide.TOP, WallSide.BOTTOM]
    )(mock_stop_wall)

    async def mock_all_walls(wall):
        pass

    sprite.when_touching_wall()(mock_all_walls)


def test_event_component_update_collisions_touching():
    sprite1 = play.new_box(color="red", x=0, y=0, width=20, height=20)
    sprite2 = play.new_box(color="blue", x=0, y=0, width=20, height=20)

    sprite1.start_physics()
    sprite2.start_physics()

    @sprite1.when_touching(sprite2)
    def touching_cb():
        pass

    @sprite1.when_touching_wall
    def touching_wall_cb(wall):
        pass

    sprite2.physics = None
    sprite1_is_touching = True
    sprite1.is_touching = lambda x: sprite1_is_touching

    sprite1.events.update_collisions()

    # Needs to process touching once
    assert id(sprite2) in sprite1.events._touching_callback

    sprite1_is_touching = False
    sprite1.events.update_collisions()

    assert id(sprite2) not in sprite1.events._touching_callback


def test_event_component_update_collisions_stopped():
    sprite1 = play.new_box(color="red", x=0, y=0, width=20, height=20)
    sprite2 = play.new_box(color="blue", x=0, y=0, width=20, height=20)

    sprite1.start_physics()
    sprite2.start_physics()

    @sprite1.when_stopped_touching(sprite2)
    def stopped_cb():
        pass

    @sprite1.when_stopped_touching_wall
    def stopped_wall_cb(wall):
        pass

    sprite2.physics = None
    sprite1_is_touching = True
    sprite1.is_touching = lambda x: sprite1_is_touching

    sprite1.events.update_collisions()

    # Registers as touching first
    assert id(sprite2) in sprite1.events._touching_callback

    # And then un-touches to trigger stopped
    sprite1_is_touching = False
    sprite1.events.update_collisions()

    assert id(sprite2) not in sprite1.events._touching_callback
    assert id(sprite2) in sprite1.events._stopped_callback
