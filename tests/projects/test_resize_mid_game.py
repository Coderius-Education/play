"""Resizing the window while a game is running.

The walls a ball bounces off are pymunk bodies built from the screen size, and
anchored widgets are positioned from it every frame. A resize therefore has to
rebuild both. Getting it half right is the interesting failure: the picture
stretches while the ball keeps bouncing off where the wall used to be, so the
game looks fine and plays wrong.

The unit test for anchors checks the sprite moves. This checks the physics
moved with it.
"""

import pygame
import pytest

import play
from play.io.screen import screen
from tests.projects.conftest import add_safety_timeout

max_frames = 400


def _post_resize(width, height):
    pygame.event.post(pygame.event.Event(pygame.VIDEORESIZE, {"w": width, "h": height}))


@pytest.mark.xfail(
    strict=True,
    reason=(
        "create_walls() runs once at import and is never called again. The "
        "VIDEORESIZE handler updates screen.width/height and the display but "
        "leaves the pymunk walls at the original size, so after a resize the "
        "ball bounces off a boundary that is no longer where the window ends. "
        "Pre-existing on master. The fix is not a re-call: create_walls() "
        "appends to globals_list.walls, so rebuilding needs the old wall "
        "bodies removed from the space first"
    ),
)
def test_walls_follow_a_resize():
    """A ball must bounce off the new right wall, not the old one.

    The screen starts 800 wide (right edge at x=400) and grows to 1200 (right
    edge at x=600). A ball sent right after the resize should travel past the
    old boundary — if it turns around at 400, the walls never moved.
    """
    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=400, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    furthest = []

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()

        _post_resize(1200, 800)
        for _ in range(3):
            await play.animate()

        for _ in range(120):
            await play.animate()
            furthest.append(ball.x)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert furthest, "the game never ran"
    assert screen.width == 1200, "the resize event should have widened the screen"
    assert max(furthest) > 400, (
        "the ball never passed the old right wall, so the walls did not move "
        f"with the screen (furthest x was {max(furthest):.0f})"
    )


def test_a_ball_is_still_contained_after_a_resize():
    """Whatever the walls do, the ball must not escape entirely.

    This passes today for the wrong reason — the ball is held by the stale
    wall at the old screen edge, not by one matching the new size. It is kept
    as the safety property: a resize must never leave the playfield open.
    """
    ball = play.new_circle(color="black", x=0, y=0, radius=10)
    ball.start_physics(
        obeys_gravity=False, x_speed=400, y_speed=0, friction=0, mass=10, bounciness=1.0
    )

    positions = []

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        _post_resize(1200, 800)
        for _ in range(200):
            await play.animate()
            positions.append(ball.x)
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert positions, "the game never ran"
    assert max(positions) < 620, (
        "the ball left the screen entirely, so the new right wall is missing "
        f"(furthest x was {max(positions):.0f})"
    )


def test_an_anchored_widget_follows_a_resize():
    """A HUD pinned to a corner must still be in the corner afterwards."""
    score = play.new_text(words="0", x=10, y=10, anchor="top-right")

    before = []
    after = []

    @play.when_program_starts
    async def driver():
        for _ in range(3):
            await play.animate()
        before.append((score.x, score.y))

        _post_resize(1200, 800)
        for _ in range(5):
            await play.animate()
        after.append((score.x, score.y))
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert before and after
    assert after[0] != before[0], (
        f"a top-right anchored sprite should have moved with the screen, "
        f"but stayed at {before[0]}"
    )
    assert (
        after[0][0] > before[0][0]
    ), "a wider screen should push a right-anchored sprite further right"
