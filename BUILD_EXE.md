# Building the .exe (Windows)

This app is 100% Python: Flask backend, the agent/pentest logic, and a pywebview
desktop shell. Build it the same way as the notes-maker:

1. **Install Python 3.11+ on the Windows machine**, then:
   ```
   pip install -r requirements.txt
   ```

2. **Install Nmap** from https://nmap.org/download.html — during setup, keep
   "Add Nmap to PATH" ticked. The app looks for `nmap.exe` on PATH automatically;
   if you installed it somewhere else, set an environment variable:
   ```
   setx NMAP_PATH "C:\Path\To\nmap.exe"
   ```

3. **Test it first without packaging:**
   ```
   python app.py
   ```
   A window titled "Digital Doppelganger Trap" should open with two tabs
   (Company Portal / Defender Monitor / Split view).

4. **Build the .exe:**
   ```
   pyinstaller main.spec
   ```
   The finished app is at `dist/DigitalDoppelgangerTrap/DigitalDoppelgangerTrap.exe`.
   Copy that whole `DigitalDoppelgangerTrap` folder when you move it to another PC
   (it's a one-folder build, not fully single-file, because pywebview needs its
   runtime files next to the exe).

## What's new vs the original web version

- **`app.py`** – new desktop entry point (pywebview window + the same Flask app).
- **`app_paths.py`** – new helper so the packaged exe finds its templates and
  writes the activity log to `%APPDATA%\DoppelgangerTrap\` (so it survives
  between runs, same idea as the notes-maker's persistence).
- **`agent.py`** – every risk-score point now carries a *reason*. `build_summary()`
  turns the recorded reasons into the Summary panel (headline, scored indicators,
  narrative, decoy activity, recommendations). **Redirect threshold raised from
  40 to 70.**
- **`pentest.py`** – new "Penetration" module: runs `nmap -sT -sV --top-ports 1000`
  against the intruder's IP automatically the moment they're trapped, in a
  background thread so the app never freezes. Flags common high-risk ports
  (SSH, RDP, SMB, databases, etc).
- **`templates/monitor.html`** – two new live sections: **Summary** and
  **Penetration**, each with a manual "Re-scan" button.
- **`templates/shell.html`** – new tabbed window (Portal / Monitor / Split)
  used by the desktop app.
- **`main.py`** – threaded Flask server (`threaded=True`) so the app can still
  serve pages while a scan runs; `/monitor` and `/api/*` are blocked from
  anything but `127.0.0.1` so an attacker on the network can't see the backend.

## A note on the nmap scan

Scanning only makes sense against machines you're authorised to test. For the
hackathon demo, scan your own lab VM or a teammate's machine on the same
network with their knowledge — not a random visitor's IP. If you demo on one
laptop (attacker and server are the same machine), nmap will also "find" your
own app's port — that's expected and not a bug, see the Summary vs Penetration
sections handle it independently.

## Deploying the web version (e.g. Render)

This is separate from the .exe build above — use this if you want a public URL
judges can visit, instead of (or alongside) the desktop app.

1. Push this `app` folder to a GitHub repo.
2. On Render (render.com): **New +** -> **Web Service** -> connect that repo.
3. Settings:
   - **Build Command:** `pip install -r requirements-web.txt`
   - **Start Command:** `gunicorn main:app --bind 0.0.0.0:$PORT --threads 8 --timeout 120`
     (same as the included `Procfile`, in case Render auto-detects it instead)
4. Add an environment variable: **MONITOR_KEY** = (any secret string you pick,
   e.g. `zh-defender-2026`). This replaces the "localhost only" rule for
   `/monitor` and `/api/*` once the app is on the internet — visit
   `https://your-app.onrender.com/monitor?key=zh-defender-2026` once, and a
   cookie remembers you after that so you don't need `?key=...` every time.
5. Deploy. Render gives you a URL like `https://your-app.onrender.com`.
6. Nmap is **not** installed on Render's free tier, so the Penetration section
   will show its "nmap not found" message there rather than a real scan — this
   is expected, not a bug. Run the Penetration demo locally (via `app.py` or
   `main.py` on your own laptop, where nmap IS installed) if you want to show
   a live scan to judges, and use the Render URL for the rest of the demo.
