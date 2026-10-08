"""
main.py – Digital Doppelganger Trap (web backend)

Run as a desktop app:  python app.py      (native window, builds into an .exe)
Run as a plain server: python main.py     (open http://127.0.0.1:5000 in a browser)
"""

import ipaddress
import os
import secrets

from flask import Flask, abort, redirect, render_template, request, session, url_for

from agent import AgentDefender
from app_paths import resource_path
from decoy import DecoyEnvironment
from fingerprint import collect_fingerprint
from logger import TrapLogger
from pentest import AUTO_SCAN, PenTester
from real_system import RealSystem

app = Flask(__name__, template_folder=resource_path("templates"))
app.secret_key = secrets.token_hex(16)

logger = TrapLogger()
agent = AgentDefender(logger)
decoy = DecoyEnvironment(logger)
real = RealSystem()
pen = PenTester(logger)

# Valid credentials for normal user
VALID_USERS = {
    "hamid": "pass111",
    "zaynab": "pass222",
    "khuld": "pass333"
}

# Pages only the defender should see.
DEFENDER_PATHS = ("/monitor", "/api/", "/app")

# Locally (no MONITOR_KEY set) we lock these to 127.0.0.1, same as before.
# When deployed (e.g. on Render), set a MONITOR_KEY environment variable and
# visit /monitor?key=<that value> once — a cookie then remembers you for the
# session, so you don't have to put the key in the URL every time.
MONITOR_KEY = os.environ.get("MONITOR_KEY", "").strip()


@app.before_request
def defender_only():
    if not request.path.startswith(DEFENDER_PATHS):
        return

    if MONITOR_KEY:
        supplied = request.args.get("key") or request.cookies.get("monitor_key")
        if supplied != MONITOR_KEY:
            abort(404)
        return  # key checked on every request; the cookie is set below for convenience

    try:
        if not ipaddress.ip_address(request.remote_addr or "").is_loopback:
            abort(404)
    except ValueError:
        abort(404)


@app.after_request
def remember_monitor_key(resp):
    if MONITOR_KEY and request.path.startswith(DEFENDER_PATHS) and request.args.get("key") == MONITOR_KEY:
        resp.set_cookie("monitor_key", MONITOR_KEY, httponly=True, samesite="Lax")
    return resp


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        actor = username or "unknown_actor"
        fp = collect_fingerprint(request)

        if username in VALID_USERS and VALID_USERS[username] == password:
            # Legitimate login
            agent.observe(actor, "normal_login")
            session["actor"] = actor
            session["trapped"] = False
            return redirect(url_for("dashboard"))
        else:
            # Failed login
            trapped = agent.observe(actor, "failed_login",
                                    extra={"fp": fp, "known_user": username in VALID_USERS})
            agent.store_fingerprint(actor, fp)

            if trapped:
                # Intruder confirmed -> start the Penetration (nmap) scan on their IP in the background
                if AUTO_SCAN:
                    pen.start(actor, fp.get("ip", ""))
                session["actor"] = actor
                session["trapped"] = True
                return redirect(url_for("dashboard"))
            else:
                return render_template("login.html", error="Invalid credentials. Try again.")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    actor = session.get("actor")
    if not actor:
        return redirect(url_for("login"))

    trapped = agent.is_trapped(actor) or session.get("trapped", False)

    if trapped:
        employees = decoy.get_employees(actor)
        payments = decoy.get_payments(actor)
        agent.note_decoy_access(actor, "employee_records.db")
        agent.note_decoy_access(actor, "customer_payments.db")
        return render_template("decoy_dashboard.html",
                               actor=actor,
                               employees=employees,
                               payments=payments,
                               message="Welcome back! (You are inside the DECOY)")
    else:
        employees = real.get_employees()
        return render_template("real_dashboard.html",
                               actor=actor,
                               employees=employees)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ========== BACKEND MONITOR (defender only) ==========
@app.route("/monitor")
def monitor():
    return render_template("monitor.html")


@app.route("/app")
def shell():
    """Single-window view used by the desktop app: Portal / Monitor / Split tabs."""
    return render_template("shell.html")


@app.route("/api/status")
def api_status():
    return {
        "logs": logger.get_entries(),
        "risk_scores": agent.get_risk_report(),
        "trapped": list(agent.trapped_actors),
        "fingerprints": agent.fingerprints,
        "login_attempts": getattr(agent, "login_attempts", {}),
        "summaries": agent.get_summaries(),     # AI explanation: why each user was flagged
        "pentest": pen.get_all(),               # nmap results per intruder
    }


def _require_monitor_header():
    # A custom header forces a CORS preflight, so other websites can't trigger these POSTs.
    if request.headers.get("X-Doppel") != "1":
        abort(403)


@app.route("/api/rescan", methods=["POST"])
def api_rescan():
    _require_monitor_header()
    actor = (request.get_json(silent=True) or {}).get("actor", "")
    fp = agent.fingerprints.get(actor)
    if not fp or not agent.is_trapped(actor):
        abort(404)
    started = pen.start(actor, fp.get("ip", ""), force=True)
    return {"started": started}


@app.route("/api/reset", methods=["POST"])
def api_reset():
    _require_monitor_header()
    agent.reset()
    pen.reset()
    return {"ok": True}


if __name__ == "__main__":
    print("=" * 60)
    print("  DIGITAL DOPPELGANGER TRAP – Web Demo")
    print("  Frontend : http://127.0.0.1:5000")
    print("  Backend  : http://127.0.0.1:5000/monitor")
    print("=" * 60)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False, threaded=True)
