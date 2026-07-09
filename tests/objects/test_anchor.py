import pytest
import play
from play.io.screen import screen


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def _settled(sprite):
    """Call update() twice so rect dimensions from frame 1 feed into frame 2 anchor."""
    sprite.update()
    sprite.update()
    return sprite


# ── Edge-based anchor semantics ───────────────────────────────────────────────
# ox / oy are pixel distances from the screen border.
# After two updates the relevant EDGE of the sprite sits at that distance.


@pytest.mark.parametrize(
    "anchor,ox,oy,check",
    [
        ("top-left", 0, 0, lambda b: (b.rect.left, b.rect.top)),
        ("top-center", 0, 0, lambda b: (b.rect.centerx, b.rect.top)),
        ("top-right", 0, 0, lambda b: (b.rect.right, b.rect.top)),
        ("center-left", 0, 0, lambda b: (b.rect.left, b.rect.centery)),
        ("center", 0, 0, lambda b: (b.rect.centerx, b.rect.centery)),
        ("center-right", 0, 0, lambda b: (b.rect.right, b.rect.centery)),
        ("bottom-left", 0, 0, lambda b: (b.rect.left, b.rect.bottom)),
        ("bottom-center", 0, 0, lambda b: (b.rect.centerx, b.rect.bottom)),
        ("bottom-right", 0, 0, lambda b: (b.rect.right, b.rect.bottom)),
    ],
)
def test_all_anchor_positions_zero_offset(anchor, ox, oy, check):
    box = play.new_box("red", width=50, height=50, anchor=anchor, x=ox, y=oy)
    _settled(box)
    got_x, got_y = check(box)
    # At zero offset the relevant edge or center should sit exactly at the
    # screen border (or screen center for "center" anchors).
    if "left" in anchor:
        assert got_x == pytest.approx(0, abs=1)
    elif "right" in anchor:
        assert got_x == pytest.approx(screen.width, abs=1)
    elif anchor in ("top-center", "bottom-center", "center"):
        assert got_x == pytest.approx(screen.width / 2, abs=1)

    if "top" in anchor:
        assert got_y == pytest.approx(0, abs=1)
    elif "bottom" in anchor:
        assert got_y == pytest.approx(screen.height, abs=1)
    elif anchor in ("center-left", "center-right", "center"):
        assert got_y == pytest.approx(screen.height / 2, abs=1)


def test_anchor_top_left_with_offset():
    box = play.new_box("red", width=50, height=50, anchor="top-left", x=20, y=15)
    _settled(box)
    assert box.rect.left == pytest.approx(20, abs=1)
    assert box.rect.top == pytest.approx(15, abs=1)


def test_anchor_top_right_with_offset():
    box = play.new_box("red", width=50, height=50, anchor="top-right", x=10, y=10)
    _settled(box)
    assert box.rect.right == pytest.approx(screen.width - 10, abs=1)
    assert box.rect.top == pytest.approx(10, abs=1)


def test_anchor_bottom_center_with_offset():
    box = play.new_box("red", width=50, height=50, anchor="bottom-center", x=0, y=20)
    _settled(box)
    assert box.rect.centerx == pytest.approx(screen.width / 2, abs=1)
    assert box.rect.bottom == pytest.approx(screen.height - 20, abs=1)


def test_anchor_text_no_crash():
    # Text.__init__ pre-renders so its rect is real before the game loop starts;
    # edge placement should be correct from the very first game-loop update().
    text = play.new_text("HUD", anchor="top-left", x=5, y=5)
    text.update()
    assert text.rect.left == pytest.approx(5, abs=1)
    assert text.rect.top == pytest.approx(5, abs=1)


def test_center_anchor_uses_play_coords():
    # "center" keeps center-based semantics: ox/oy are play-coordinate offsets.
    box = play.new_box("red", width=50, height=50, anchor="center", x=30, y=20)
    _settled(box)
    assert box.rect.centerx == pytest.approx(screen.width / 2 + 30, abs=1)
    assert box.rect.centery == pytest.approx(screen.height / 2 - 20, abs=1)


def test_no_anchor_leaves_xy_unchanged():
    box = play.new_box(x=50, y=30)
    assert box.x == pytest.approx(50, abs=1)
    assert box.y == pytest.approx(30, abs=1)


def test_anchored_sprite_with_gravity_physics_falls():
    # Regression: the anchor must not pin a free (gravity-obeying) physics
    # body in place by snapping position and zeroing velocity every frame.
    from play.physics import physics_space
    from play.core.sprites_loop import update_sprite_physics

    box = play.new_box("red", width=50, height=50, anchor="top-center")
    _settled(box)
    y_anchored = box.y
    box.start_physics()  # dynamic body that obeys gravity
    for _ in range(10):
        physics_space.step(1 / 60.0)
        update_sprite_physics(box)
        box.update()
    assert box.y < y_anchored
    assert box.physics._pymunk_body.velocity.y < 0
