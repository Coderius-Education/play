"""Tests for the Slider widget."""

import pytest
import play
from play.io.mouse import mouse
from play.core.mouse_loop import mouse_state


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_slider_creation():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    assert s.min_value == 0
    assert s.max_value == 100
    assert s.value == 50


def test_slider_clamps_initial_value():
    s = play.new_slider(min_value=0, max_value=10, value=200)
    assert s.value == 10


def test_slider_clamps_initial_value_low():
    s = play.new_slider(min_value=5, max_value=10, value=1)
    assert s.value == 5


def test_slider_value_setter_clamps():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    s.value = 150
    assert s.value == 100
    s.value = -10
    assert s.value == 0


def test_slider_min_value_setter():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    s.min_value = 60
    assert s.value == 60  # clamped up


def test_slider_max_value_setter():
    s = play.new_slider(min_value=0, max_value=100, value=80)
    s.max_value = 70
    assert s.value == 70  # clamped down


def test_slider_when_changed_fires():
    s = play.new_slider(min_value=0, max_value=100, value=50)
    results = []
    s.when_changed(results.append)
    s.value = 75
    assert results == [75]


def test_slider_when_changed_rejects_async():
    s = play.new_slider()
    with pytest.raises(TypeError):

        @s.when_changed
        async def bad(v):
            pass


def test_slider_disabled_default_false():
    s = play.new_slider()
    assert s.disabled is False


def test_slider_disabled_setter():
    s = play.new_slider()
    s.disabled = True
    assert s.disabled is True


def test_slider_alive():
    s = play.new_slider()
    assert s.alive()


def test_slider_hit_shape_matches_size():
    # Regression: a 0x0 rect at construction gave a degenerate point hit-shape,
    # so only dead-centre clicks could grab the slider.
    s = play.new_slider(width=200, height=20, thumb_radius=12)
    bb = s.physics._pymunk_shape.bb
    assert (bb.right - bb.left) > 0
    assert (bb.top - bb.bottom) > 0


# ── drag interaction ──────────────────────────────────────────────────────────
# The 800x600 test display puts x=0 at screen centre. For a slider at x=0 with
# width=200 and thumb_radius=12, the usable track spans mouse.x ∈ [-88, +88],
# so mouse.x=-88 → min, mouse.x=+88 → max, mouse.x=0 → midpoint.


def _start_drag(slider):
    mouse.x, mouse.y = 0, 0
    mouse._is_clicked = True
    mouse_state.click_happened = True
    slider.update()
    mouse_state.click_happened = False


def test_slider_drag_to_far_right_sets_max():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse.x = 88
    s.update()
    assert s.value == 100


def test_slider_drag_to_far_left_sets_min():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse.x = -88
    s.update()
    assert s.value == 0


def test_slider_drag_stops_on_mouse_release():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    _start_drag(s)
    mouse._is_clicked = False  # released
    mouse.x = 88
    s.update()
    assert s.value == 50  # not dragging → unchanged


def test_slider_drag_fires_when_changed():
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    seen = []
    s.when_changed(seen.append)
    _start_drag(s)
    mouse.x = 88
    s.update()
    assert 100 in seen


def test_slider_step_quantizes_dragged_value():
    s = play.new_slider(
        min_value=0, max_value=100, value=0, x=0, y=0, width=200, step=25
    )
    _start_drag(s)  # mouse.x=0 → midpoint 50 (already a multiple of 25)
    mouse.x = -35  # ~raw 30 → snaps to nearest 25
    s.update()
    assert s.value == 25


def test_slider_no_drag_without_prior_grab():
    # Moving the mouse over the slider without a click must not change the value.
    s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
    mouse.x, mouse.y = 88, 0
    s.update()
    assert s.value == 50


def test_slider_image_rendered():
    s = play.new_slider()
    assert s.image is not None
    assert s.image.get_width() > 0 and s.image.get_height() > 0


def _thumb_mean_x(surface, rgb):
    """Mean x of pixels matching *rgb* (the thumb colour), or None if absent."""
    tr, tg, tb = rgb[:3]
    xs = []
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            c = surface.get_at((x, y))
            if c.r == tr and c.g == tg and c.b == tb and c.a != 0:
                xs.append(x)
    return sum(xs) / len(xs) if xs else None


def test_slider_thumb_moves_with_value():
    # Give the thumb a colour distinct from the fill so we can locate it.
    from play.utils import color_name_to_rgb

    thumb_rgb = color_name_to_rgb("red")

    def thumb_x(value):
        s = play.new_slider(
            min_value=0,
            max_value=100,
            value=value,
            width=200,
            thumb_color="red",
            fill_color="blue",
            track_color="lightgray",
        )
        return _thumb_mean_x(s.image, thumb_rgb)

    left, mid, right = thumb_x(0), thumb_x(50), thumb_x(100)
    assert left is not None and mid is not None and right is not None
    assert left < mid < right


def test_slider_show_value_widens_image():
    # Regression: show_value must include the label in the surface, not clip it
    # off the right edge.
    plain = play.new_slider(width=200, value=100, show_value=False)
    labelled = play.new_slider(width=200, value=100, show_value=True)
    assert labelled.image is not None
    assert labelled.image.get_width() > plain.image.get_width()


def test_slider_clone():
    s = play.new_slider(min_value=10, max_value=90, value=40)
    c = s.clone()
    assert c.min_value == 10
    assert c.max_value == 90
    assert c.value == 40


def test_slider_fractional_range_renders_full_fill():
    # Regression: max(1, span) drew the thumb/fill halfway for sub-1 ranges.
    from tests.conftest import count_color

    s = play.new_slider(
        min_value=0,
        max_value=0.5,
        value=0.5,
        fill_color="red",
        thumb_color="blue",
        track_color="lightgray",
    )
    filled = count_color(s.image, (255, 0, 0))
    # At value == max the fill spans (nearly) the whole 200px track.
    assert filled > 150 * s._height
