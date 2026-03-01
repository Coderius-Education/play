import pytest
import play
import warnings

from play.utils import experimental


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_experimental_decorator():
    """
    The @experimental decorator should emit a FutureWarning on instantiation
    and mark the class docstring as experimental.
    """

    @experimental
    class MyWidget:
        """A test widget."""

        def __init__(self, value):
            self.value = value

    assert "EXPERIMENTAL" in MyWidget.__doc__

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        obj = MyWidget(42)

    assert obj.value == 42
    assert len(w) == 1
    assert issubclass(w[0].category, FutureWarning)
    assert "MyWidget" in str(w[0].message)
    assert "experimental" in str(w[0].message).lower()


def test_experimental_decorator_no_docstring():
    """@experimental on a class without a docstring should add a default one."""

    @experimental
    class Bare:
        def __init__(self):
            pass

    assert "EXPERIMENTAL" in Bare.__doc__


def test_architecture_trap_double_start_program():
    """
    If a user calls `play.start_program()` twice, it shouldn't crash
    the asyncio event loops, it should just throw a helpful Exception.
    """
    play.api.utils._program_started = True
    try:
        with pytest.raises(Exception) as exc_info:
            play.start_program()

        assert (
            "already" in str(exc_info.value).lower()
            or "running" in str(exc_info.value).lower()
        )
    finally:
        play.api.utils._program_started = False
