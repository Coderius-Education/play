import pytest
import warnings
import pygame
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_add_warns_when_called_directly():
    """Calling sprite.add() directly should emit a UserWarning."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    group = pygame.sprite.Group()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        box.add(group)

    assert len(w) >= 1
    assert any(issubclass(warning.category, UserWarning) for warning in w)
    assert any("pygame internal" in str(warning.message).lower() for warning in w)


def test_add_internal_warns_when_called_directly():
    """Calling sprite.add_internal() directly should emit a UserWarning."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    group = pygame.sprite.Group()

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        box.add_internal(group)

    assert len(w) >= 1
    assert any(issubclass(warning.category, UserWarning) for warning in w)


def test_remove_internal_warns_when_called_directly():
    """Calling sprite.remove_internal() directly should emit a UserWarning."""
    box = play.new_box(color="red", x=0, y=0, width=10, height=10)
    group = pygame.sprite.Group()
    # First add to the group so we can remove
    group.add(box)

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        box.remove_internal(group)

    assert len(w) >= 1
    assert any(issubclass(warning.category, UserWarning) for warning in w)
    assert any("remove" in str(warning.message).lower() for warning in w)
