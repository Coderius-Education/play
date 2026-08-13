"""Tests for pairs of features used together.

Single-feature tests were not what found the collision bug fixed in this
branch. That needed one sprite carrying two ``when_touching`` callbacks at
once — an intersection. Features are usually written and tested one at a
time, so the seams between them are where bugs survive.

Each test here combines two features that a real game combines routinely.
"""

import pytest

import play
from play.globals import globals_list
from play.io.screen import screen
from tests.conftest import click_at


# ---------------------------------------------------------------------------
# keyboard focus x sprite lifecycle
# ---------------------------------------------------------------------------


def test_removing_a_focused_text_input_releases_focus():
    """A removed field must not keep the keyboard.

    Focus is global state pointing at one widget. If it survives the widget,
    every keystroke goes to something the user cannot see and the game's own
    key callbacks stay suspended forever.
    """
    from play.objects import text_input_registry as registry

    field = play.new_text_input(x=0, y=0)
    registry.focus(field)
    assert globals_list.focused_text_input is field

    field.remove()

    assert globals_list.focused_text_input is None


def test_hiding_a_focused_text_input_releases_focus():
    """Same reasoning as removal: an invisible field must not eat the keyboard."""
    from play.objects import text_input_registry as registry

    field = play.new_text_input(x=0, y=0)
    registry.focus(field)

    field.hide()

    assert globals_list.focused_text_input is None


def test_disabling_a_focused_text_input_releases_focus():
    from play.objects import text_input_registry as registry

    field = play.new_text_input(x=0, y=0)
    registry.focus(field)

    field.disabled = True

    assert globals_list.focused_text_input is None


# ---------------------------------------------------------------------------
# collisions x physics lifecycle
# ---------------------------------------------------------------------------


def test_removing_a_sprite_stops_its_collision_callbacks():
    """A partner that no longer exists must not keep triggering callbacks.

    pymunk never sends a separate event for a shape it no longer owns, so a
    callback left registered against a removed sprite either never completes
    or fires forever, depending on which side vanished.
    """
    touches = []

    ball = play.new_circle(color="black", x=-100, y=0, radius=10)
    block = play.new_box(color="blue", x=0, y=0, width=40, height=400)
    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(block)
    def touched():
        touches.append(len(touches))
        block.remove()

    @play.when_program_starts
    async def budget():
        for _ in range(400):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert touches, "the ball never reached the block"
    # After the block is gone the callback has nothing to fire against. The
    # frame it was removed in may still finish dispatching, so allow that one.
    assert len(touches) <= globals_list.num_sim_steps, (
        f"the callback kept firing after its partner was removed "
        f"({len(touches)} times)"
    )


def test_restarting_physics_while_touching_does_not_wedge():
    """start_physics() on a touching sprite replaces its pymunk shape.

    The old shape's active-touch record has to go with it, or the sprite is
    left permanently 'touching' something it has since left.
    """
    events = []

    ball = play.new_circle(color="black", x=-100, y=0, radius=10)
    block = play.new_box(color="blue", x=0, y=0, width=40, height=400)
    ball.start_physics(
        obeys_gravity=False, x_speed=200, y_speed=0, friction=0, mass=10, bounciness=1.0
    )
    block.start_physics(
        obeys_gravity=False, can_move=False, friction=0, mass=10, bounciness=1.0
    )

    @ball.when_touching(block)
    def touched():
        if not events:
            events.append("touch")
            # Swap the ball's shape out mid-contact, then send it away.
            ball.start_physics(
                obeys_gravity=False,
                x_speed=-300,
                y_speed=0,
                friction=0,
                mass=10,
                bounciness=1.0,
            )

    @ball.when_stopped_touching(block)
    def separated():
        events.append("separate")
        play.stop_program()

    @play.when_program_starts
    async def budget():
        for _ in range(500):
            await play.animate()
        play.stop_program()

    play.start_program()

    assert "touch" in events, "the ball never reached the block"
    assert "separate" in events, (
        "the ball left the block but never reported separating — its touch "
        "record survived the shape swap"
    )


# ---------------------------------------------------------------------------
# layers x click ownership
# ---------------------------------------------------------------------------


# Widget state is asserted rather than when_clicked callbacks: those dispatch
# through the event loop, which is not running in a click_at() unit test, so a
# callback-based assertion here would be checking nothing.
#
# test_click_ownership.py already covers the plain topmost-widget case. What it
# does not cover is a top widget that is present but not interactive, which is
# what these two add.


def test_hidden_widget_does_not_take_clicks_from_the_one_below():
    """Hiding the top widget must hand clicks back, not swallow them.

    Ownership is resolved from the widgets under the cursor. If a hidden one
    still wins that contest the click vanishes: the user sees nothing on top,
    clicks the thing they can see, and nothing happens.
    """
    lower = play.new_checkbox(x=0, y=0, size_px=40, layer=10)
    upper = play.new_checkbox(x=0, y=0, size_px=40, layer=20)

    upper.hide()
    click_at(0, 0, lower, upper)

    assert (
        lower.checked is True
    ), "with the top widget hidden the click should fall through"
    assert upper.checked is False, "a hidden widget should not react to clicks"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "a disabled widget still wins click ownership and then declines to "
        "act, so the click reaches nothing. resolve_click_owner() selects on "
        "`s._is_widget and mouse.is_touching(s)`; is_touching excludes hidden "
        "sprites, which is why hiding works, but nothing excludes disabled "
        "ones — contradicting that function's own docstring, which says the "
        "top-most *interactive* widget takes the click"
    ),
)
def test_disabled_widget_does_not_take_clicks_from_the_one_below():
    """A disabled widget is visible but inert — it must not block either."""
    lower = play.new_checkbox(x=0, y=0, size_px=40, layer=10)
    upper = play.new_checkbox(x=0, y=0, size_px=40, layer=20)

    upper.disabled = True
    click_at(0, 0, lower, upper)

    assert upper.checked is False, "a disabled widget should not react to clicks"
    assert lower.checked is True, "a disabled widget should not swallow the click"


# ---------------------------------------------------------------------------
# anchors x screen size
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "anchor", ["top-left", "top-right", "bottom-left", "bottom-right"]
)
def test_anchored_sprite_follows_a_screen_resize(anchor):
    """An anchored sprite is positioned against the screen edge every frame.

    Resizing therefore has to move it. A sprite that keeps its old coordinates
    ends up adrift from the corner it was pinned to, which is the whole point
    of anchoring it.
    """
    box = play.new_box(color="red", x=10, y=10, width=20, height=20, anchor=anchor)

    box.update()
    before = (box.x, box.y)

    screen.width, screen.height = 1024, 768
    screen.update_display()
    box.update()
    after = (box.x, box.y)

    assert before != after, (
        f"a sprite anchored {anchor!r} should move when the screen resizes, "
        f"but stayed at {before}"
    )
