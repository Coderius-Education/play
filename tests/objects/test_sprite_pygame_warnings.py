import pytest
import warnings
import pygame
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_pygame_internal_calls_do_not_warn():
    """play's own sprite handling must not warn the user about itself.

    is_called_from_pygame() used to require "site-packages" in the caller's
    path. Debian and Ubuntu install to dist-packages, so the check never
    matched there and ordinary sprite creation and removal warned on every
    call — invisible on Windows and in venvs, noisy for exactly the beginners
    this library is aimed at.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        box = play.new_box(color="red", x=0, y=0, width=10, height=10)
        group = pygame.sprite.Group()
        group.add(box)  # pygame calls add_internal for us
        group.remove(box)  # and remove_internal
        box.remove()

    internal_warnings = [
        warning for warning in w if "pygame internal" in str(warning.message).lower()
    ]
    assert not internal_warnings, [str(x.message) for x in internal_warnings]


def test_detection_is_not_fooled_by_a_pygame_shaped_path():
    """A user path containing "pygame" must not count as pygame itself.

    Otherwise the guard rail goes silent for anyone working in, say,
    ~/pygame-tutorial/ — the warning would be suppressed exactly where a
    beginner is most likely to need it.
    """
    from play.utils import is_called_from_pygame

    source = "def check(fn):\n    return fn()\n"
    namespace = {}
    exec(compile(source, "/home/student/pygame-tutorial/game.py", "exec"), namespace)

    assert namespace["check"](is_called_from_pygame) is False


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
