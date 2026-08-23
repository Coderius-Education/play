"""Property-based (hypothesis) tests for widget invariants.

Covers:
- Sprite anchor placement (all 9 anchors, arbitrary offsets and box sizes)
- Slider value clamping and when_changed firing semantics
- TextInput cursor/value invariants under random editing sequences
"""

import pygame
import pytest

from hypothesis import HealthCheck, given, settings, strategies as st

import play
from play.io.screen import screen


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


# ── anchor placement ──────────────────────────────────────────────────────────

ANCHORS = [
    "top-left",
    "top-center",
    "top-right",
    "center-left",
    "center",
    "center-right",
    "bottom-left",
    "bottom-center",
    "bottom-right",
]

# rect coordinates are ints and _apply_anchor mixes float offsets with integer
# rect halves, so allow a small rounding tolerance.
_TOL = 2


def _assert_anchor_placement(box, anchor, ox, oy):
    """Assert the settled rect matches _apply_anchor's edge semantics.

    For edge anchors ox/oy are pixel distances inward from the anchored screen
    border; for the "center" axis they are play-coordinate offsets from the
    screen centre (play y is positive upward).
    """
    parts = anchor.split("-")
    y_key = parts[0]
    x_key = parts[1] if len(parts) > 1 else "center"

    if x_key == "left":
        assert box.rect.left == pytest.approx(ox, abs=_TOL)
    elif x_key == "right":
        assert box.rect.right == pytest.approx(screen.width - ox, abs=_TOL)
    else:  # "center"
        assert box.rect.centerx == pytest.approx(screen.width / 2 + ox, abs=_TOL)

    if y_key == "top":
        assert box.rect.top == pytest.approx(oy, abs=_TOL)
    elif y_key == "bottom":
        assert box.rect.bottom == pytest.approx(screen.height - oy, abs=_TOL)
    else:  # "center"
        assert box.rect.centery == pytest.approx(screen.height / 2 - oy, abs=_TOL)


@given(
    anchor=st.sampled_from(ANCHORS),
    ox=st.floats(min_value=-500, max_value=500, allow_nan=False, allow_infinity=False),
    oy=st.floats(min_value=-500, max_value=500, allow_nan=False, allow_infinity=False),
    width=st.integers(min_value=1, max_value=300),
    height=st.integers(min_value=1, max_value=300),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_anchor_placement_and_stability(anchor, ox, oy, width, height):
    box = play.new_box("red", width=width, height=height, anchor=anchor, x=ox, y=oy)
    try:
        # Two updates: frame 1 renders the rect, frame 2 applies the anchor
        # with real half-dimensions.
        box.update()
        box.update()

        _assert_anchor_placement(box, anchor, ox, oy)

        # Idempotence: re-applying the anchor must not move the sprite.
        settled = (box.rect.x, box.rect.y, box.rect.width, box.rect.height)
        box.update()
        box.update()
        assert (box.rect.x, box.rect.y, box.rect.width, box.rect.height) == settled
        _assert_anchor_placement(box, anchor, ox, oy)
    finally:
        box.remove()


# ── slider clamping ───────────────────────────────────────────────────────────

_bounded_floats = st.floats(
    min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False
)


@given(
    bounds=st.tuples(_bounded_floats, _bounded_floats).filter(lambda b: b[0] < b[1]),
    initial=_bounded_floats,
    new_values=st.lists(_bounded_floats, min_size=1, max_size=5),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_slider_value_always_clamped_and_change_fires_on_real_change(
    bounds, initial, new_values
):
    min_v, max_v = bounds
    slider = play.new_slider(min_value=min_v, max_value=max_v, value=initial)
    try:
        # Construction clamps the initial value into range.
        assert min_v <= slider.value <= max_v
        assert slider.value == max(min_v, min(max_v, initial))

        fired = []
        slider.when_changed(lambda v: fired.append(v))

        model = slider.value
        expected_changes = 0
        for v in new_values:
            clamped = max(min_v, min(max_v, v))
            if clamped != model:
                expected_changes += 1
                model = clamped
            slider.value = v
            assert min_v <= slider.value <= max_v
            assert slider.value == model

        # when_changed fires exactly once per transition to a different
        # clamped value — never for a set that clamps to the current value.
        assert len(fired) == expected_changes
        assert fired == [v for v in fired if min_v <= v <= max_v]
    finally:
        slider.remove()


# ── text input editing invariants ─────────────────────────────────────────────

_printable_char = st.characters(min_codepoint=32, max_codepoint=126)

_edit_ops = st.lists(
    st.tuples(
        st.sampled_from(
            ["left", "right", "home", "end", "backspace", "delete", "type"]
        ),
        _printable_char,
    ),
    min_size=0,
    max_size=30,
)

_OP_KEYS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "home": pygame.K_HOME,
    "end": pygame.K_END,
    "backspace": pygame.K_BACKSPACE,
    "delete": pygame.K_DELETE,
}


def _keydown(key, mod=0):
    return pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": mod, "unicode": ""})


@given(
    initial=st.text(alphabet=_printable_char, max_size=40),
    ops=_edit_ops,
)
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_text_input_editing_keeps_cursor_and_value_consistent(initial, ops):
    ti = play.new_text_input(value=initial)
    try:
        # Model the field: a string and a cursor index, updated exactly per the
        # documented semantics of each editing operation.
        model_text = initial
        model_cursor = len(initial)
        assert ti._cursor_pos == model_cursor

        for op, ch in ops:
            if op == "type":
                ti._handle_text_input(ch)
                model_text = model_text[:model_cursor] + ch + model_text[model_cursor:]
                model_cursor += 1
            else:
                ti._handle_keydown(_keydown(_OP_KEYS[op]))
                if op == "left":
                    model_cursor = max(0, model_cursor - 1)
                elif op == "right":
                    model_cursor = min(len(model_text), model_cursor + 1)
                elif op == "home":
                    model_cursor = 0
                elif op == "end":
                    model_cursor = len(model_text)
                elif op == "backspace":
                    if model_cursor > 0:
                        model_text = (
                            model_text[: model_cursor - 1] + model_text[model_cursor:]
                        )
                        model_cursor -= 1
                elif op == "delete":
                    if model_cursor < len(model_text):
                        model_text = (
                            model_text[:model_cursor] + model_text[model_cursor + 1 :]
                        )

            # Core invariant: the cursor never leaves the value's bounds.
            assert 0 <= ti._cursor_pos <= len(ti.value)
            # The value is exactly the model's prefix + typed char + suffix
            # composition — no lost or duplicated characters.
            assert ti.value == model_text
            assert ti._cursor_pos == model_cursor
    finally:
        ti.remove()


# ── widget geometry: the hit-shape must follow the drawn widget ───────────────
#
# These guard the class of bug where a widget's image and its pymunk hit-shape
# disagree: the visible control has dead zones, or clicks land on empty space
# beside it.

# Latin-1/Latin Extended-A, so accented characters a Dutch teaching library
# actually uses are exercised, not just ASCII.
_label_char = st.characters(
    min_codepoint=32, max_codepoint=0x017F, blacklist_categories=("Cs",)
)


@given(
    size_px=st.integers(min_value=8, max_value=80),
    label=st.text(alphabet=_label_char, max_size=20),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_checkbox_centre_is_clickable_and_its_surroundings_are_not(size_px, label):
    from play.io.mouse import mouse

    checkbox = play.new_checkbox(label=label, x=0, y=0, size_px=size_px)
    try:
        checkbox.update()
        mouse.x, mouse.y = 0, 0
        assert mouse.is_touching(checkbox), "the centre of a widget is always clickable"

        # Twice the half-width is comfortably outside whatever the label made.
        mouse.x, mouse.y = checkbox.width + 10, 0
        assert not mouse.is_touching(
            checkbox
        ), "clicks beside the widget must not reach it"
    finally:
        checkbox.remove()


@given(size=st.integers(min_value=25, max_value=400))
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_checkbox_image_and_hit_shape_scale_together(size):
    from play.io.mouse import mouse

    checkbox = play.new_checkbox(label="Geluid", x=0, y=0, size_px=24)
    try:
        checkbox.update()
        base_width = checkbox.image.get_width()

        checkbox.size = size
        checkbox.update()
        assert checkbox.image.get_width() == pytest.approx(
            base_width * size / 100, abs=2
        ), "the drawn image must scale with size"

        # The hit-shape scales from the same factor, so the centre still hits.
        mouse.x, mouse.y = 0, 0
        assert mouse.is_touching(checkbox)
    finally:
        checkbox.remove()


# ── progress bar: percentage stays a fraction under any bound mutation ────────


@given(
    bounds=st.tuples(_bounded_floats, _bounded_floats).filter(lambda b: b[0] < b[1]),
    initial=_bounded_floats,
    mutations=st.lists(
        st.tuples(st.sampled_from(["min", "max", "value"]), _bounded_floats),
        min_size=1,
        max_size=6,
    ),
)
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_progress_bar_percentage_stays_a_fraction(bounds, initial, mutations):
    min_v, max_v = bounds
    bar = play.new_progress_bar(min_value=min_v, max_value=max_v, value=initial)
    try:
        attr_for = {"min": "min_value", "max": "max_value", "value": "value"}
        for field, value in mutations:
            setattr(bar, attr_for[field], value)
            # Bounds may never cross: a negative span silently pins the bar.
            assert bar.min_value <= bar.max_value
            assert 0.0 <= bar.percentage <= 1.0
            assert bar.min_value <= bar.value <= bar.max_value
    finally:
        bar.remove()
