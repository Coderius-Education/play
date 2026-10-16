# /// script
# dependencies = ["numpy", "pygame-ce", "pymunk"]
# ///
"""A short play game that tells the page whether it ran: CI runs it with pygbag and Pyodide."""

import asyncio
import sys
import traceback

try:
    from platform import window as pygbag_page
except ImportError:
    pygbag_page = None


class _AlsoToConsole:
    """Write to pygbag's terminal and to the browser console, where CI reads it."""

    def __init__(self, stream):
        self.stream = stream

    def write(self, text):
        pygbag_page.console.log(text)
        return self.stream.write(text)

    def flush(self):
        self.stream.flush()


def _window():
    """Return the browser's window: pygbag's platform.window or Pyodide's js module."""
    if pygbag_page is not None:
        return pygbag_page
    import js  # pylint: disable=import-outside-toplevel

    return js


def report(result):
    """Print the result and put its first line in the page title, where CI reads it."""
    print(result)
    if sys.platform == "emscripten":
        _window().document.title = result.splitlines()[0]


def main():
    """Drop a box onto a floor, with an async contact callback, and report after 60 frames."""
    import play  # pylint: disable=import-outside-toplevel
    from play.globals import globals_list  # pylint: disable=import-outside-toplevel
    from play.loop import get_loop  # pylint: disable=import-outside-toplevel

    box = play.new_box(color="red", y=100, width=40, height=40)
    box.start_physics()
    floor = play.new_box(color="black", y=40, width=200, height=20)
    floor.start_physics(can_move=False)
    frames = []
    contact = []

    @box.when_touching(floor)
    async def landed():
        if not contact:
            contact.append(f"landed={len(frames)}")
            await play.animate()
            contact.append(f"resumed={len(frames)}")

    @play.repeat_forever
    def check():
        frames.append(1)
        if len(frames) == 60:
            fine = box.y < 100 and len(contact) == 2
            report(
                f"PLAY-{'OK' if fine else 'FAIL'} frames={len(frames)} "
                f"y={box.y:.0f} {' '.join(contact)}"
            )
            play.stop_program()

    async def report_an_error():
        while len(frames) < 60:
            if globals_list.error_shown:
                report(f"PLAY-FAIL error after {len(frames)} frames")
                return
            await asyncio.sleep(0.1)

    get_loop().create_task(report_an_error())
    play.start_program()


if pygbag_page is not None:
    sys.stdout = _AlsoToConsole(sys.stdout)
    sys.stderr = _AlsoToConsole(sys.stderr)

try:
    main()
except Exception:  # pylint: disable=broad-exception-caught
    report("PLAY-FAIL\n" + traceback.format_exc())
