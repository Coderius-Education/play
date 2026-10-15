# /// script
# dependencies = ["numpy", "pymunk"]
# ///
"""A short play game that tells the page whether it ran: CI builds it with pygbag."""

import sys

if sys.platform == "emscripten":
    import platform

    class _AlsoToConsole:
        """Write to the terminal and to the browser console, where CI reads it."""

        def __init__(self, stream):
            self.stream = stream

        def write(self, text):
            platform.window.console.log(text)
            return self.stream.write(text)

        def flush(self):
            self.stream.flush()

    sys.stdout = _AlsoToConsole(sys.stdout)
    sys.stderr = _AlsoToConsole(sys.stderr)

import play  # pylint: disable=wrong-import-position

box = play.new_box(color="red", y=100, width=40, height=40)
box.start_physics()
frames = []


def report(result):
    """Print the result and put it in the page title, where the browser test reads it."""
    print(result)
    if sys.platform == "emscripten":
        platform.window.document.title = result


@play.repeat_forever
def check():
    frames.append(1)
    if len(frames) == 60:
        landed = box.y < 100
        report(f"PLAY-{'OK' if landed else 'FAIL'} frames={len(frames)} y={box.y:.0f}")
        play.stop_program()


play.start_program()
