"""
app.py – Desktop entry point.

Runs the same Flask app from main.py inside a native window (pywebview) instead of a
browser tab, and opens the Portal + Monitor as two windows side by side, same spirit as
the notes-maker .exe: double-click, one window, no terminal needed.

Build with:  pyinstaller main.spec
"""

import socket
import sys
import threading
import time

import webview

from main import app


def _free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _run_flask(port):
    # Quiet the Flask/Werkzeug startup banner inside the packaged .exe
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(host="127.0.0.1", port=port, debug=False, use_reloader=False, threaded=True)


def main():
    port = _free_port()
    t = threading.Thread(target=_run_flask, args=(port,), daemon=True)
    t.start()

    # wait for the server instead of a fixed sleep
    for _ in range(100):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            break
        except OSError:
            time.sleep(0.1)

    base = f"http://127.0.0.1:{port}"
    webview.create_window("Digital Doppelganger Trap", f"{base}/app",
                          width=1280, height=800, min_size=(900, 600))
    webview.start()


if __name__ == "__main__":
    main()
