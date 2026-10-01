"""Console entry point for the Icare Web app.

Run with ``python run_webapp.py`` (development) or as the bundled
``IcareWeb.exe`` on Windows.
"""

from __future__ import annotations

import logging
import sys
import webbrowser
from threading import Timer

from webapp import create_app

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 5000


def _open_browser() -> None:
    try:
        webbrowser.open(f"http://{HOST}:{PORT}")
    except Exception:
        logger.exception("Could not open browser automatically")


def main() -> None:
    app = create_app()
    is_frozen = getattr(sys, "frozen", False)
    debug = not is_frozen
    # When running the packaged exe, also pop the browser open after 1 s
    if is_frozen:
        Timer(1.0, _open_browser).start()
    logger.info("Icare Web running on http://%s:%s (debug=%s)", HOST, PORT, debug)
    # use_reloader=False avoids the dev-server double-instantiation that would
    # spawn two DMX controllers and two live-player threads.
    app.run(host=HOST, port=PORT, debug=debug, use_reloader=False)


if __name__ == "__main__":
    main()
