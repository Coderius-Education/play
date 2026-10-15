# /// script
# dependencies = ["numpy", "pymunk"]
# ///
"""A short play game that tells the page whether it ran: CI builds it with pygbag."""

import sys

import play

box = play.new_box(color="red", y=100, width=40, height=40)
box.start_physics()
frames = []


def report(result):
    """Print the result and put it in the page title, where the browser test reads it."""
    print(result)
    if sys.platform == "emscripten":
        import platform

        platform.window.document.title = result


@play.repeat_forever
def check():
    frames.append(1)
    if len(frames) == 60:
        landed = box.y < 100
        report(f"PLAY-{'OK' if landed else 'FAIL'} frames={len(frames)} y={box.y:.0f}")
        play.stop_program()


play.start_program()
