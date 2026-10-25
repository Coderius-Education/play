import asyncio

import pytest

import play
from play.callback.collision_callbacks import WallSide


def run_frames(frames):
    """Run the real game loop for a number of frames."""
    counted = [0]

    @play.repeat_forever
    def step():
        counted[0] += 1
        if counted[0] == frames:
            play.stop_program()

    play.start_program()


def test_is_clicked_on_the_component_is_what_the_sprite_reports():
    sprite = play.new_circle(color="red", x=0, y=0, radius=10)
    assert sprite.is_clicked is False

    sprite.events.is_clicked = True

    assert sprite.is_clicked is True


def test_a_touching_record_can_be_looked_up_and_cleared():
    sprite = play.new_circle(radius=10)

    def on_touch():
        pass

    sprite.events.set_touching("key", on_touch)

    assert sprite.events.get_touching("key") is on_touch
    assert sprite.events.get_touching("other key", "default") == "default"
    sprite.events.clear_touching("key")
    assert sprite.events.get_touching("key") is None


def test_a_new_contact_runs_once_in_its_first_frame_and_every_frame_after():
    sprite = play.new_circle(radius=10)

    def on_touch():
        pass

    sprite.events.set_touching("key", on_touch)

    assert sprite.events.new_touching_callbacks() == [on_touch]
    assert sprite.events.touching_callbacks() == []
    assert sprite.events.touching_callbacks() == [on_touch]


def test_touching_a_hidden_or_removed_sprite_runs_nothing():
    sprite = play.new_circle(radius=10)
    hidden = play.new_box()
    removed = play.new_box()
    sprite.events.set_touching("hidden", lambda: None, other=hidden)
    sprite.events.set_touching("removed", lambda: None, other=removed)

    hidden.hide()
    removed.remove()

    assert sprite.events.new_touching_callbacks() == []
    assert sprite.events.touching_callbacks() == []


def test_stopped_callbacks_are_kept_until_cleared():
    sprite = play.new_circle(radius=10)

    def on_stop():
        pass

    sprite.events.set_stopped("key", on_stop)

    assert sprite.events.stopped_callbacks() == [on_stop]
    sprite.events.clear_all_stopped()
    assert sprite.events.stopped_callbacks() == []


def test_click_callbacks_get_the_sprite_only_when_asked():
    sprite = play.new_circle(color="red", x=0, y=0, radius=10)
    calls = []

    async def plain():
        calls.append("clicked")

    async def with_sprite(sprite):
        calls.append(sprite)

    async def released():
        calls.append("released")

    async def released_with_sprite(sprite):
        calls.append(("released", sprite))

    asyncio.run(sprite.when_clicked(plain)())
    asyncio.run(sprite.when_clicked(with_sprite, call_with_sprite=True)())
    asyncio.run(sprite.when_click_released(released)())
    asyncio.run(
        sprite.when_click_released(released_with_sprite, call_with_sprite=True)()
    )

    assert calls == ["clicked", sprite, "released", ("released", sprite)]


def test_when_touching_returns_a_runnable_wrapper_and_links_the_sprites():
    sprite1 = play.new_box(color="red", x=0, y=0, width=10, height=10)
    sprite2 = play.new_box(color="blue", x=100, y=100, width=10, height=10)
    sprite1.start_physics()
    sprite2.start_physics()
    calls = []

    async def touching():
        calls.append("touching")

    async def stopped():
        calls.append("stopped")

    asyncio.run(sprite1.when_touching(sprite2)(touching)())
    asyncio.run(sprite1.when_stopped_touching(sprite2)(stopped)())

    assert calls == ["touching", "stopped"]
    assert sprite1 in sprite2.events._dependent_sprites


def test_remove_cleans_up_dependent_sprites():
    """sprite.remove() must remove self from every target's _dependent_sprites
    and clear its callbacks from callback_manager."""
    from play.callback import callback_manager, CallbackType

    sprite1 = play.new_box(color="red", x=0, y=0, width=10, height=10)
    sprite2 = play.new_box(color="blue", x=100, y=100, width=10, height=10)
    sprite1.start_physics()
    sprite2.start_physics()

    async def mock_touching():
        pass

    sprite1.when_touching(sprite2)(mock_touching)
    assert sprite1 in sprite2.events._dependent_sprites

    sprite1_id = id(sprite1)
    sprite1.remove()

    assert sprite1 not in sprite2.events._dependent_sprites
    assert not callback_manager.get_callback(CallbackType.WHEN_TOUCHING, sprite1_id)


def test_wall_callbacks_run_only_for_the_walls_they_name():
    box = play.new_box(x=play.screen.left, width=40, height=40)
    box.start_physics(obeys_gravity=False, x_speed=200)
    ran = []

    @box.when_touching_wall(wall=WallSide.LEFT)
    def left(wall):
        ran.append(("left", wall))

    @box.when_touching_wall(wall=WallSide.RIGHT)
    def right(wall):
        ran.append(("right", wall))

    @box.when_touching_wall(wall=[WallSide.TOP, WallSide.BOTTOM])
    def top_or_bottom(wall):
        ran.append(("top or bottom", wall))

    @box.when_stopped_touching_wall()
    def any_wall_stopped(wall):
        ran.append(("any stopped", wall))

    run_frames(30)

    assert set(ran) == {("left", WallSide.LEFT), ("any stopped", WallSide.LEFT)}


@pytest.mark.parametrize(
    "register, event",
    [
        ("when_clicked", "WHEN_CLICKED_SPRITE"),
        ("when_click_released", "WHEN_CLICK_RELEASED_SPRITE"),
    ],
)
def test_a_click_callback_runs_again_on_the_next_click(register, event):
    import play.loop
    from play.callback import callback_manager, CallbackType

    sprite = play.new_circle(radius=10)
    calls = []
    getattr(sprite, register)(lambda: calls.append(True))

    for _ in range(2):
        callback_manager.run_callbacks(
            getattr(CallbackType, event), callback_discriminator=id(sprite)
        )
        for _ in range(3):
            play.loop.get_loop().run_until_complete(asyncio.sleep(0))

    assert calls == [True, True]
