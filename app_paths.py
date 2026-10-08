r"""
app_paths.py – where files live, both in `python main.py` mode and when frozen into an .exe.

resource_path(): read-only bundled files (templates). Inside a PyInstaller exe these are unpacked to sys._MEIPASS.
data_dir():      writable files (activity log). Inside the exe we use %APPDATA%\DoppelgangerTrap so the log
                 survives between runs (the _MEIPASS folder is deleted on exit).
"""
import os
import sys

FROZEN = getattr(sys, "frozen", False)


def resource_path(*parts):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def data_dir():
    if FROZEN:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        folder = os.path.join(base, "DoppelgangerTrap")
    else:
        folder = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(folder, exist_ok=True)
    return folder
