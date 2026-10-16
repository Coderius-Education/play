# /// script
# dependencies = ["numpy", "pygame-ce", "pymunk"]
# ///
"""A short play game that tells the page whether it ran: CI runs it with pygbag and Pyodide."""

import asyncio
import sys
import traceback

if sys.platform == "emscripten":
    try:
        from platform import window as page
    except ImportError:
        import js as page

    class _AlsoToConsole:
        """Write to the terminal and to the browser console, where CI reads it."""

        def __init__(self, stream):
            self.stream = stream

        def write(self, text):
            page.console.log(text)
            return self.stream.write(text)

        def flush(self):
            self.stream.flush()

    sys.stderr = _AlsoToConsole(sys.stderr)


def report(result):
    """Print the result and put it in the page title, where the browser test reads it."""
    print(result)
    if sys.platform == "emscripten":
        page.console.log(result)
        page.document.title = result.splitlines()[0]


try:
    import play
    from play.globals import globals_list
    from play.loop import get_loop

    box = play.new_box(color="red", y=100, width=40, height=40)
    box.start_physics()
    frames = []

    @play.repeat_forever
    def check():
        frames.append(1)
        if len(frames) == 60:
            landed = box.y < 100
            report(
                f"PLAY-{'OK' if landed else 'FAIL'} frames={len(frames)} y={box.y:.0f}"
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
except Exception:  # pylint: disable=broad-exception-caught
    report("PLAY-FAIL\n" + traceback.format_exc())
