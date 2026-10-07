import pytest
import play
from play.io.screen import screen
from play.callback import callback_manager, CallbackType


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_when_resized_registers_callback():
    """screen.when_resized() should register a WHEN_RESIZED callback."""

    @screen.when_resized
    def on_resize():
        pass

    callbacks = callback_manager.get_callbacks(CallbackType.WHEN_RESIZED)
    assert len(callbacks) >= 1


def test_when_resized_leaves_the_function_callable():
    # Students call their layout function once at start-up as well.
    ran = []

    @screen.when_resized
    def layout():
        ran.append(True)
        return "laid out"

    assert layout() == "laid out"
    assert ran == [True]
