import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_syntax_case_insensitivity_colors():
    """
    Beginners might capitalize colors differently (e.g. 'RED', 'Red', 'red').
    The library should normalize them and succeed.
    """
    box1 = play.new_box(color="RED", x=0, y=0, width=10, height=10)
    box2 = play.new_box(color="Red", x=10, y=0, width=10, height=10)
    box3 = play.new_box(color="red", x=20, y=0, width=10, height=10)

    # All should successfully bind the RGB translation without KeyError
    assert box1.color == "red"
    assert box2.color == box1.color
    assert box3.color == box1.color


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
