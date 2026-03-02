import pytest
import play
from play.io.screen import screen


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_resizable_default_false():
    """Screen should not be resizable by default."""
    assert screen.resizable is False


def test_resizable_setter():
    """Setting screen.resizable should store the value."""
    screen.resizable = True
    assert screen.resizable is True
    screen.resizable = False
    assert screen.resizable is False
