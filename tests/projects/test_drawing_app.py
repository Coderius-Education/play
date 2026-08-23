"""A drawing app — hold the mouse down and drag to leave a trail.

Covers the mouse-drag pattern (polling ``play.mouse.is_clicked`` and creating
sprites as the pointer moves) that no other project test exercises, and the
sprite-accumulation it implies.
"""

from tests.conftest import (
    count_color,
    post_mouse_motion,
    post_mouse_down,
    post_mouse_up,
)
from tests.projects.conftest import add_safety_timeout

max_frames = 400


def test_drawing_app():
    import play
    from play.io.screen import screen
    from play.globals import globals_list
    from play.utils import color_name_to_rgb

    dots = []
    seen = {}

    @play.when_program_starts
    async def driver():
        def screen_xy(x, y):
            return int(screen.width / 2 + x), int(screen.height / 2 - y)

        async def drag_across(xs, y):
            """Press, move through xs leaving a dot each frame, then release."""
            post_mouse_motion(*screen_xy(xs[0], y))
            await play.animate()
            post_mouse_down(*screen_xy(xs[0], y))
            await play.animate()
            for x in xs:
                post_mouse_motion(*screen_xy(x, y))
                await play.animate()
                # The beginner pattern: poll the button state each frame.
                if play.mouse.is_clicked:
                    dots.append(
                        play.new_circle(
                            color="purple", x=play.mouse.x, y=play.mouse.y, radius=8
                        )
                    )
            post_mouse_up(*screen_xy(xs[-1], y))
            await play.animate()

        purple = color_name_to_rgb("purple")
        for _ in range(5):
            await play.animate()
        seen["purple_before"] = count_color(globals_list.display, purple)

        await drag_across([-150, -100, -50, 0, 50, 100, 150], 0)
        seen["dots_after_drag"] = len(dots)
        seen["xs"] = [round(d.x) for d in dots]
        await play.animate()
        seen["purple_after"] = count_color(globals_list.display, purple)

        # Moving with the button released must not draw.
        before = len(dots)
        for x in (-150, 0, 150):
            post_mouse_motion(*screen_xy(x, 120))
            await play.animate()
            if play.mouse.is_clicked:
                dots.append(play.new_circle(color="purple", x=play.mouse.x, y=0))
        seen["dots_after_hover"] = len(dots) - before
        play.stop_program()

    add_safety_timeout(max_frames)
    play.start_program()

    assert seen["purple_before"] == 0, "nothing should be drawn before the drag"
    assert seen["dots_after_drag"] >= 5, (
        "dragging across the screen should leave a trail, got "
        f"{seen['dots_after_drag']} dots"
    )
    assert seen["purple_after"] > 0, "the trail should actually be drawn on screen"
    assert seen["xs"] == sorted(
        seen["xs"]
    ), "the trail should follow the drag, left to right"
    assert seen["xs"][0] < seen["xs"][-1], "the trail should span the drag"
    assert (
        seen["dots_after_hover"] == 0
    ), "moving the mouse without holding the button must not draw"
