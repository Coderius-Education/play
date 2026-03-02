import pytest
import play
from play.io.screen import screen
from play.callback import callback_manager, CallbackType


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_when_resized_registers_callback():
    """screen.when_resized() should register a WHEN_RESIZED callback."""
    called = []

    @screen.when_resized
    def on_resize():
        called.append(True)

    callbacks = callback_manager.get_callbacks(CallbackType.WHEN_RESIZED)
    assert len(callbacks) >= 1
