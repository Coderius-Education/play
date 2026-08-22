"""Regression tests for widget construction, layout, and hit-shape sizing.

Covers three classes of bug:

* A widget built while a click is still live must not activate itself.
* An anchored sprite must track its own size changes in the same frame.
* A widget's drawn image and its pymunk hit-shape must scale together.
"""

import pytest
import pygame
import play
from play.io.mouse import mouse
from play.io.screen import screen
from play.core.mouse_loop import mouse_state


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _begin_click(x, y):
    """Put the frame into the state it has midway through handling a click."""
    mouse.x, mouse.y = x, y
    mouse._is_clicked = True
    mouse_state.click_happened = True
    mouse_state.resolve_click_owner()


def _end_click():
    mouse_state.clear()
    mouse._is_clicked = False


# ── widgets created during a click must not activate themselves ───────────────


def test_checkbox_created_during_click_does_not_toggle():
    _begin_click(0, 0)
    try:
        cb = play.new_checkbox(x=0, y=0, size_px=24)
        assert cb.checked is False
    finally:
        _end_click()


def test_radio_button_created_during_click_does_not_select():
    _begin_click(0, 0)
    try:
        g = play.new_radio_group()
        r = play.new_radio_button("A", value="a", group=g, x=0, y=0)
        assert r._selected is False
        assert g.selected_value is None
    finally:
        _end_click()


def test_slider_created_during_click_does_not_start_drag():
    # Mouse sits left of centre, so a spurious drag would also move the value.
    _begin_click(-50, 0)
    try:
        s = play.new_slider(min_value=0, max_value=100, value=50, x=0, y=0, width=200)
        assert s._dragging is False
        assert s.value == 50
    finally:
        _end_click()


# ── anchored sprites track their own size changes ─────────────────────────────


def test_anchor_tracks_content_size_change_within_one_frame():
    # Regression: _apply_anchor() ran before _render(), so it used the previous
    # frame's rect. A HUD read-out that changes every frame — the canonical use
    # for an edge anchor — was therefore never at its requested offset.
    label = play.new_text(words="5", anchor="top-right", x=10, y=10)
    label.update()
    label.update()
    assert label.rect.right == pytest.approx(screen.width - 10, abs=1)

    label.words = "100000"
    label.update()
    assert label.rect.right == pytest.approx(screen.width - 10, abs=1)


# ── image and hit-shape scale together ────────────────────────────────────────


def test_checkbox_size_scales_the_drawn_image():
    cb = play.new_checkbox(x=0, y=0, size_px=24)
    cb.update()
    base_w = cb.image.get_width()
    cb.size = 200
    cb.update()
    assert cb.image.get_width() > base_w


# ── progress bar bounds stay ordered ──────────────────────────────────────────


def test_progress_bar_min_value_cannot_cross_max():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    pb.min_value = 200
    assert pb.min_value <= pb.max_value


def test_progress_bar_max_value_cannot_cross_min():
    pb = play.new_progress_bar(min_value=0, max_value=100, value=50)
    pb.max_value = -50
    assert pb.min_value <= pb.max_value


# ── hidden sprites are non-interactive both ways ──────────────────────────────


def test_hidden_sprite_does_not_collide_with_other_sprite():
    a = play.new_box(color="red", x=0, y=0, width=50, height=50)
    b = play.new_box(color="blue", x=0, y=0, width=50, height=50)
    assert b.is_touching(a) is True
    a.hide()
    # Hiding pauses physics, so the shape leaves the space but keeps its last
    # transform; the query must not keep reporting the stale contact.
    assert b.is_touching(a) is False
    assert a.is_touching(b) is False


# ── disabled text input is visually distinct ──────────────────────────────────


def test_disabled_text_input_is_dimmed():
    enabled = play.new_text_input(value="abc", x=0, y=0)
    disabled = play.new_text_input(value="abc", x=0, y=150, disabled=True)
    enabled.update()
    disabled.update()
    enabled_px = pygame.image.tobytes(enabled.image, "RGBA")
    disabled_px = pygame.image.tobytes(disabled.image, "RGBA")
    assert enabled_px != disabled_px
