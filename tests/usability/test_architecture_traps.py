import pytest
import play


@pytest.fixture(autouse=True)
def setup_play(clean_play_state):
    pass


def test_architecture_trap_double_start_program():
    """
    If a user calls `play.start_program()` twice, it shouldn't crash
    the asyncio event loops, it should just throw a helpful Exception.
    """
    play.globals.globals_list.program_state = play.globals.ProgramState.RUNNING
    try:
        with pytest.raises(Exception) as exc_info:
            play.start_program()

        assert (
            "already" in str(exc_info.value).lower()
            or "running" in str(exc_info.value).lower()
        )
    finally:
        play.globals.globals_list.program_state = play.globals.ProgramState.NOT_STARTED
