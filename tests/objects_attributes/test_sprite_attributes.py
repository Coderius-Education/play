"""What a sprite is made with is what it reports, before and after the game runs."""

import pytest

import play

MADE_WITH = {
    "new_box": {
        "color": "blue",
        "x": 10,
        "y": 20,
        "width": 50,
        "height": 30,
        "border_color": "red",
        "border_width": 3,
        "border_radius": 5,
        "transparency": 80,
        "size": 120,
        "angle": 30,
        "layer": 2,
    },
    "new_circle": {
        "color": "yellow",
        "x": 15,
        "y": 25,
        "radius": 30,
        "border_color": "green",
        "border_width": 2,
        "transparency": 60,
        "size": 150,
        "angle": 90,
        "layer": 3,
    },
    "new_text": {
        "words": "hello",
        "x": 5,
        "y": 10,
        "font": "default",
        "font_size": 40,
        "color": "purple",
        "angle": 45,
        "transparency": 70,
        "size": 110,
        "layer": 4,
    },
}


def reported(sprite, names):
    """The sprite's properties, with floats from the physics body rounded."""
    values = {name: getattr(sprite, name) for name in names}
    return {n: round(v) if isinstance(v, float) else v for n, v in values.items()}


@pytest.mark.parametrize("factory", MADE_WITH, ids=MADE_WITH)
def test_a_sprite_reports_what_it_was_made_with_while_the_game_runs(factory):
    expected = MADE_WITH[factory]
    sprite = getattr(play, factory)(**expected)
    seen = {"made": reported(sprite, expected)}
    frames = [0]

    @play.repeat_forever
    def check():
        frames[0] += 1
        if frames[0] == 5:
            seen["running"] = reported(sprite, expected)
            play.stop_program()

    play.start_program()

    assert seen["made"] == expected
    assert seen["running"] == expected
