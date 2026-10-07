"""start_program() returns however the program stops, even in the first frame.

The first frame runs inside start_program()'s run_until_complete. A stop
there that did not mark the program as stopped left start_program() waiting
in run_forever() on a loop with no frame scheduled: the window froze and the
process never ended (#231).
"""

AFTER_START = "play.start_program()\nprint('returned')\nos._exit(0)\n"


def test_an_error_in_the_first_frame_ends_the_program(run_script):
    # Raises once only: a second error in frame 2 would stop the loop anyway.
    printed = run_script(
        "frames = [0]\n"
        "@play.repeat_forever\n"
        "def loop():\n"
        "    frames[0] += 1\n"
        "    if frames[0] == 1:\n"
        "        score = undefined_name\n" + AFTER_START
    )
    assert printed == ["returned"]


def test_an_error_in_when_touching_in_the_first_frame_ends_the_program(run_script):
    printed = run_script(
        "a = play.new_circle(radius=20)\n"
        "b = play.new_circle(x=10, radius=20)\n"
        "@a.when_touching(b)\n"
        "def hit():\n"
        "    score = undefined_name\n" + AFTER_START
    )
    assert printed == ["returned"]


def test_closing_the_window_before_the_first_frame_ends_the_program(run_script):
    # A student clicks the close button while the script is still loading.
    printed = run_script(
        "import pygame\n"
        "play.new_circle()\n"
        "pygame.event.post(pygame.event.Event(pygame.QUIT))\n" + AFTER_START
    )
    assert printed == ["returned"]


def test_an_error_in_a_later_frame_still_ends_the_program(run_script):
    printed = run_script(
        "frames = [0]\n"
        "@play.repeat_forever\n"
        "def loop():\n"
        "    frames[0] += 1\n"
        "    if frames[0] == 3:\n"
        "        score = undefined_name\n" + AFTER_START
    )
    assert printed == ["returned"]
