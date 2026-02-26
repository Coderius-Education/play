import pytest
import play
import warnings


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_architecture_trap_spawning_in_loop():
    """
    If a beginner puts `play.new_box()` inside a `repeat_forever` loop,
    they will spawn 60 boxes a second and freeze their computer (memory bomb).
    The library should theoretically detect geometry creation during the active
    run loop and emit a Warning or throw an Exception.
    """
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # We manually simulate the engine being in 'running' mode
        play.api.utils._program_started = True

        try:
            play.new_box(color="red", x=0, y=0, width=10, height=10)

            # If the engine successfully threw an exception, we pass.
            # If it just warned, we check the warnings list.
            if len(w) == 0:
                pytest.fail(
                    "Engine failed to warn the user about spawning sprites mid-game-loop!"
                )

            assert (
                "spawn" in str(w[-1].message).lower()
                or "loop" in str(w[-1].message).lower()
                or "start" in str(w[-1].message).lower()
            )
        except Exception as e:
            assert (
                "spawn" in str(e).lower()
                or "loop" in str(e).lower()
                or "start" in str(e).lower()
            )

        finally:
            play.api.utils._program_started = False


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
