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

import play
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
        "shape_registry": len(collision_registry.shape_registry),
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
