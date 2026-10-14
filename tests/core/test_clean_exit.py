"""A program that imports play exits with its own exit code, not a crash in pymunk (#232)."""

import os
import subprocess
import sys

import pytest

import play

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(play.__file__)))

STOP_IN_THE_FIRST_FRAME = """
@play.repeat_forever
def stop():
    play.stop_program()

play.start_program()
"""


@pytest.mark.parametrize(
    "body, exit_code",
    [
        ("", 0),
        ("print(undefined_name)\n", 1),
        (STOP_IN_THE_FIRST_FRAME, 0),
    ],
    ids=["import only", "error at top level", "game stops"],
)
def test_the_process_exits_with_the_programs_own_code(tmp_path, body, exit_code):
    script = tmp_path / "game.py"
    script.write_text("import play\n" + body)
    env = {
        **os.environ,
        "PYTHONPATH": ROOT,
        "SDL_VIDEODRIVER": "dummy",
        "SDL_AUDIODRIVER": "dummy",
        "PYGAME_HIDE_SUPPORT_PROMPT": "1",
    }

    result = subprocess.run(
        [sys.executable, str(script)],
        timeout=30,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == exit_code, result.stderr
