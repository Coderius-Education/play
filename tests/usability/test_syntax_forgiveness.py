import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


@pytest.mark.parametrize("name", ["RED", "Red", "red", " red ", "#F00", "#ff0000"])
def test_a_color_name_draws_the_same_however_it_is_written(name):
    box = play.new_box(color=name, x=0, y=0, width=10, height=10)
    box.update()

    assert box.image.get_at(box.image.get_rect().center)[:3] == (255, 0, 0)


@pytest.mark.parametrize("name", ["light blue", "light-blue", "LightBlue"])
def test_a_two_word_color_draws_with_a_space_a_hyphen_or_neither(name):
    box = play.new_box(color=name, x=0, y=0, width=10, height=10)
    box.update()

    assert box.image.get_at(box.image.get_rect().center)[:3] == (173, 216, 230)


def test_syntax_physics_spelling_mistakes():
    """
    If a kid types `bouncinees=50` instead of `bounciness`, the engine
    should warn or raise an explicit TypeError mentioning the typo,
    rather than silently accepting it as kwargs or crashing inside Pymunk.
    """
    box = play.new_box(color="blue", x=0, y=0, width=10, height=10)

    with pytest.raises(TypeError) as exc_info:
        # Deliberate typo 'bouncinees' instead of 'bounciness'
        box.start_physics(bouncinees=50)

    assert (
        "unexpected keyword argument" in str(exc_info.value).lower()
        or "bouncinees" in str(exc_info.value).lower()
    )


def test_syntax_start_physics_empty():
    """
    Calling start_physics empty is perfectly valid, but we must ensure it defaults correctly.
    """
    box = play.new_box(color="green", x=0, y=0, width=10, height=10)
    box.start_physics()

    assert box.physics.can_move is True
    assert box.physics.bounciness == 1.0  # default
