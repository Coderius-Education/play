"""Serve a pygbag build, open it in headless Chromium and wait for the game's verdict.

Usage: python run_in_chromium.py BUILD_WEB_DIR
"""

import functools
import http.server
import sys
import threading

from playwright.sync_api import sync_playwright

TIMEOUT_MS = 180_000

TERMINAL_TEXT = """() => {
    const lines = [];
    for (const name of Object.getOwnPropertyNames(window)) {
        try {
            const value = window[name];
            const buffer = value && value.buffer && value.buffer.active;
            if (!buffer || typeof buffer.getLine !== "function") continue;
            for (let row = 0; row < buffer.length; row++) {
                const line = buffer.getLine(row);
                if (line) lines.push(line.translateToString(true));
            }
        } catch (error) {
            continue;
        }
    }
    return lines.length ? lines.join("\\n") : document.body.innerText;
}"""


def serve(directory):
    """Serve *directory* on a free local port and return the server."""
    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory=directory
    )
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def main(directory):
    server = serve(directory)
    url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
    log = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        page.on("console", lambda message: log.append(f"[console] {message.text}"))
        page.on("pageerror", lambda error: log.append(f"[pageerror] {error}"))
        page.goto(url)
        try:
            page.wait_for_function(
                "document.title.startsWith('PLAY-')", timeout=TIMEOUT_MS
            )
            title = page.title()
        except Exception as error:  # pylint: disable=broad-exception-caught
            title = f"no verdict: {error}"
        terminal = page.evaluate(TERMINAL_TEXT)
        browser.close()
    server.shutdown()

    print("\n".join(log))
    print("--- terminal ---")
    print(terminal)
    print("--- verdict ---")
    print(title)
    return 0 if title.startswith("PLAY-OK") else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
