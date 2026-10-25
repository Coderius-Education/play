"""Every sprite gets a physics body when it is made, before start_physics()."""

import pytest
import play

SPRITES = {
    "box": lambda **kw: play.new_box(width=200, height=20, **kw),
    "circle": lambda **kw: play.new_circle(radius=40, **kw),
    "text": lambda **kw: play.new_text("platform", font_size=40, **kw),
}


@pytest.mark.parametrize("make", SPRITES.values(), ids=SPRITES.keys())
def test_a_new_sprite_can_be_touched_straight_away(make):
    sprite = make(x=100, y=50)

    assert sprite.is_touching((100, 50))
    assert not sprite.is_touching((-100, 50))


@pytest.mark.parametrize("make", SPRITES.values(), ids=SPRITES.keys())
def test_a_new_sprite_stays_put_and_a_falling_ball_lands_on_it(make):
    platform = make(y=0)
    ball = play.new_circle(y=150, radius=10)
    ball.start_physics(bounciness=0)
    frames = [0]

    @play.repeat_forever
    def step():
        frames[0] += 1
        if frames[0] == 180:
            play.stop_program()

    play.start_program()

    assert (platform.x, platform.y) == (0, 0)
    assert ball.bottom >= platform.top - 2
