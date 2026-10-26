"""Hiding and showing a sprite: is_hidden, is_shown, hide() and show()."""

import pytest

import play

HIDE = {
    "hide()": lambda sprite: sprite.hide(),
    "is_hidden = True": lambda sprite: setattr(sprite, "is_hidden", True),
    "is_shown = False": lambda sprite: setattr(sprite, "is_shown", False),
}
SHOW = {
    "show()": lambda sprite: sprite.show(),
    "is_hidden = False": lambda sprite: setattr(sprite, "is_hidden", False),
    "is_shown = True": lambda sprite: setattr(sprite, "is_shown", True),
}


def test_a_new_sprite_is_shown():
    box = play.new_box()

    assert box.is_hidden is False
    assert box.is_shown is True


@pytest.mark.parametrize("hide", HIDE.values(), ids=HIDE.keys())
def test_a_hidden_sprite_draws_nothing_and_cannot_be_touched(hide):
    box = play.new_box(width=50, height=50)

    hide(box)
    box.update()

    assert box.is_hidden is True
    assert box.is_shown is False
    assert box.image.get_size() == (0, 0)
    assert not box.is_touching((0, 0))


@pytest.mark.parametrize("show", SHOW.values(), ids=SHOW.keys())
def test_a_shown_sprite_is_drawn_and_can_be_touched_again(show):
    box = play.new_box(width=50, height=50)
    box.hide()
    box.update()

    show(box)
    box.update()

    assert box.is_hidden is False
    assert box.is_shown is True
    assert box.image.get_size() == (50, 50)
    assert box.is_touching((0, 0))


def test_hiding_twice_needs_only_one_show():
    box = play.new_box(width=50, height=50)

    box.hide()
    box.hide()
    box.show()
    box.update()

    assert box.is_shown is True
    assert box.is_touching((0, 0))


def test_a_hidden_physics_sprite_stays_put_until_it_is_shown():
    box = play.new_box(y=100, width=50, height=50)
    box.start_physics()
    box.hide()
    heights = {}
    frames = [0]

    @play.repeat_forever
    def step():
        frames[0] += 1
        if frames[0] == 10:
            heights["hidden"] = box.y
            box.show()
        if frames[0] == 20:
            heights["shown"] = box.y
            play.stop_program()

    play.start_program()

    assert heights["hidden"] == 100
    assert heights["shown"] < 100
