"""Global registries must not accumulate what a game has thrown away.

play keeps several module-level registries: the sprite group, the pymunk space,
the collision callback registry, and the TextInput tab order. A game that
creates and destroys things — bullets, enemies, a settings panel opened and
closed — churns through all of them.

What leaks here is not just memory. A removed field left in the tab order means
Tab moves focus to a widget that is no longer on screen, and the keyboard
silently stops reaching the game. Leaks in these structures are behavioural
bugs, not just growth.
"""

import gc
import weakref

import pytest

import play
from play.callback import CallbackType, callback_manager
from play.globals import globals_list
from play.physics import physics_space
from play.callback.collision_callbacks import collision_registry
from play.objects import text_input_registry as registry


def _counts():
    return {
        "sprites": len(globals_list.sprites_group.sprites()),
        "bodies": len(physics_space.bodies),
        "shapes": len(physics_space.shapes),
        "tab_order": len(registry._tab_order),
        "collision_callbacks": sum(
            len(others)
            for begin in (True, False)
            for others in collision_registry.callbacks[begin].values()
        ),
    }


def test_creating_and_removing_sprites_leaves_nothing_behind():
    """500 rounds of the thing every shooter does to its bullets."""
    before = _counts()

    for _ in range(500):
        bullet = play.new_circle(color="black", x=0, y=0, radius=5)
        bullet.start_physics(obeys_gravity=False, x_speed=100)
        bullet.remove()

    after = _counts()
    assert after["sprites"] == before["sprites"]
    assert after["bodies"] == before["bodies"]
    assert after["shapes"] == before["shapes"]


def test_creating_and_removing_widgets_leaves_nothing_behind():
    """A settings panel opened and closed a hundred times."""
    before = _counts()

    for _ in range(100):
        widgets = [
            play.new_button(text="ok"),
            play.new_checkbox(label="sound"),
            play.new_slider(min_value=0, max_value=10, value=5),
            play.new_text_input(value="name"),
            play.new_dropdown(options=["a", "b"]),
        ]
        for widget in widgets:
            widget.remove()

    after = _counts()
    assert after["sprites"] == before["sprites"]
    assert after["tab_order"] == before["tab_order"], (
        "removed text inputs are still in the Tab order, so Tab would move "
        "focus to fields that are no longer on screen"
    )


def test_collision_callbacks_do_not_pile_up():
    """Registering collisions on short-lived sprites must not grow the registry."""
    before = _counts()

    for _ in range(100):
        ball = play.new_circle(color="black", x=0, y=0, radius=5)
        block = play.new_box(color="blue", x=50, y=0, width=20, height=20)
        ball.start_physics(obeys_gravity=False)
        block.start_physics(obeys_gravity=False, can_move=False)

        @ball.when_touching(block)
        def touched():
            pass

        ball.remove()
        block.remove()

    after = _counts()
    assert after["bodies"] == before["bodies"]
    assert after["shapes"] == before["shapes"]
    # remove() drops the sprite's collision callbacks; on master every round
    # left two behind, 200 after these hundred.
    assert after["collision_callbacks"] == before["collision_callbacks"]


def _with_when_touching():
    ball = play.new_circle(color="black", x=0, y=0, radius=5)
    block = play.new_box(color="blue", x=50, y=0, width=20, height=20)
    ball.start_physics(obeys_gravity=False)
    block.start_physics(obeys_gravity=False, can_move=False)

    @ball.when_touching(block)
    def touched():
        pass

    return [ball, block]


def _with_when_touching_wall():
    ball = play.new_circle(color="black", x=0, y=0, radius=5)
    ball.start_physics(obeys_gravity=False)

    @ball.when_touching_wall
    def touched(wall):
        pass

    return [ball]


def _with_when_clicked():
    box = play.new_box()

    @box.when_clicked
    def clicked():
        pass

    @box.when_click_released
    def released():
        pass

    return [box]


def _button_with_when_clicked():
    button = play.new_button("Go")

    @button.when_clicked
    def clicked():
        pass

    return [button]


@pytest.mark.parametrize(
    "make",
    [
        _with_when_touching,
        _with_when_touching_wall,
        _with_when_clicked,
        _button_with_when_clicked,
    ],
    ids=["when_touching", "when_touching_wall", "when_clicked", "button"],
)
def test_removed_sprites_with_callbacks_are_freed(make):
    """A shooter that removes its bullets must not keep them in memory.

    On master every one of these stayed alive for the rest of the program:
    the collision registry mapped each registered shape to its sprite, and
    click callbacks stayed registered under the removed sprite's id.
    """
    refs = []
    for _ in range(50):
        sprites = make()
        for sprite in sprites:
            sprite.remove()
        refs += [weakref.ref(sprite) for sprite in sprites]
    del sprites, sprite
    gc.collect()

    alive = sum(ref() is not None for ref in refs)
    assert alive == 0, f"{alive} of {len(refs)} removed sprites are still in memory"


def test_remove_drops_every_callback_registered_under_the_sprite():
    # A new sprite that CPython hands the same id() must not inherit them.
    box = _with_when_clicked()[0]
    box_id = id(box)
    # Without this the test would pass if the callbacks were filed elsewhere.
    for callback_type in (
        CallbackType.WHEN_CLICKED_SPRITE,
        CallbackType.WHEN_CLICK_RELEASED_SPRITE,
    ):
        assert callback_manager.get_callback(callback_type, box_id)
    box.remove()
    for callback_type in CallbackType:
        assert not callback_manager.get_callback(callback_type, box_id)


def test_a_sprite_can_remove_itself_inside_its_own_click():
    # remove() clears the sprite's click callbacks from inside one of them.
    # run_callbacks schedules every callback of a click as a task before any
    # of them runs, so the rest of this click still runs; a later click does
    # nothing, because a removed sprite is no longer in the loop.
    from play.io.screen import screen
    from tests.conftest import post_mouse_down, post_mouse_motion, post_mouse_up

    box = play.new_box(x=0, y=0, width=100, height=100)
    log = []

    @box.when_clicked
    def first():
        log.append("first")
        box.remove()

    @box.when_clicked
    def second():
        log.append("second")

    sx, sy = int(screen.width / 2), int(screen.height / 2)

    @play.when_program_starts
    async def drive():
        post_mouse_motion(sx, sy)
        await play.animate()
        for _ in range(2):
            post_mouse_down(sx, sy)
            await play.animate()
            post_mouse_up(sx, sy)
            await play.animate()
        play.stop_program()

    play.start_program()
    assert log == ["first", "second"]


def test_a_bullet_can_remove_itself_and_its_target_on_a_hit():
    enemy = play.new_box(x=0, y=0, width=40, height=40)
    bullet = play.new_circle(x=-100, y=0, radius=5)
    bullet.start_physics(obeys_gravity=False, x_speed=200)
    hits = []

    @bullet.when_touching(enemy)
    def hit():
        hits.append(True)
        enemy.remove()
        bullet.remove()

    frames = [0]

    @play.repeat_forever
    def tick():
        frames[0] += 1
        if frames[0] == 90:
            play.stop_program()

    play.start_program()
    assert hits == [True]
    assert not bullet.alive() and not enemy.alive()


# ---------------------------------------------------------------------------
# Tab order
# ---------------------------------------------------------------------------


def test_tab_moves_through_fields_in_order_and_wraps():
    first = play.new_text_input(x=0, y=100)
    second = play.new_text_input(x=0, y=0)
    third = play.new_text_input(x=0, y=-100)

    registry.focus(first)
    registry.focus_next()
    assert globals_list.focused_text_input is second

    registry.focus_next()
    assert globals_list.focused_text_input is third

    registry.focus_next()
    assert globals_list.focused_text_input is first, "Tab should wrap around"


def test_tab_skips_hidden_and_disabled_fields():
    """Tab must reach only fields the user can actually see and type into."""
    first = play.new_text_input(x=0, y=100)
    hidden = play.new_text_input(x=0, y=50)
    disabled = play.new_text_input(x=0, y=0)
    last = play.new_text_input(x=0, y=-100)

    hidden.hide()
    disabled.disabled = True

    registry.focus(first)
    registry.focus_next()

    assert (
        globals_list.focused_text_input is last
    ), "Tab should have skipped the hidden and disabled fields"


def test_tab_with_no_usable_field_clears_focus():
    """Every field hidden means there is nothing to focus, not a stale target."""
    only = play.new_text_input(x=0, y=0)
    registry.focus(only)
    only.hide()

    registry.focus_next()

    assert globals_list.focused_text_input is None


def test_tab_after_the_focused_field_is_removed():
    """Removing the focused field mid-game must leave Tab working."""
    first = play.new_text_input(x=0, y=100)
    second = play.new_text_input(x=0, y=0)

    registry.focus(first)
    first.remove()

    registry.focus_next()

    assert globals_list.focused_text_input is second
