"""
agent.py – Agentic Defender

Same perceive -> remember -> decide -> act loop as before, with one addition:
every point added to an actor's risk score is now recorded WITH A REASON, so the agent
can explain itself afterwards (build_summary). The summary is built only from what the
agent really observed, so it can't invent reasons.
"""

import datetime
import ipaddress
import threading
import time

RISK_WEIGHTS = {
    "failed_login": 20,
    "rapid_login_attempts": 25,
    "access_sensitive": 15,
    "normal_login": -10,
    "view_dashboard": 0,
    "repeated_failures": 15,
    "automated_client": 15,
}

REDIRECT_THRESHOLD = 70   # Raised from 40: trips after ~2 rapid or ~3 normal failed logins
RAPID_WINDOW = 15         # seconds: two failed logins closer than this count as "rapid"

# code -> (short title, explanation template)
SIGNALS = {
    "failed_login":         ("Failed login",            "Login attempt with invalid credentials"),
    "repeated_failures":    ("Repeated failures",       "Kept failing after the first wrong attempt"),
    "rapid_login_attempts": ("Rapid-fire attempts",     "Failed logins only seconds apart, typical of scripted guessing"),
    "automated_client":     ("Automated client",        "Browser fingerprint looks like a bot, not a person"),
    "normal_login":         ("Valid login",             "Correct credentials (lowers risk)"),
}


def _clock(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")


class AgentDefender:
    def __init__(self, logger):
        self.logger = logger
        self._lock = threading.RLock()
        self.reset(clear_logger=False)

    # ------------------------------------------------------------------ state
    def reset(self, clear_logger=True):
        with self._lock:
            self.risk_scores = {}
            self.trapped_actors = set()
            self.fingerprints = {}
            self.login_attempts = {}
            self.events = {}          # actor -> [ {t, clock, code, points, total, reason} ]
            self.context = {}         # actor -> {"known_user": bool}
            self.trap_time = {}       # actor -> epoch seconds
            self.decoy_access = {}    # actor -> {resource: count}
            self._last_fail = {}
        if clear_logger:
            self.logger.clear()

    def _add(self, actor, code, points, reason, now):
        self.risk_scores[actor] = self.risk_scores.get(actor, 0) + points
        self.events.setdefault(actor, []).append({
            "t": now,
            "clock": _clock(now),
            "code": code,
            "points": points,
            "total": self.risk_scores[actor],
            "reason": reason,
        })

    # --------------------------------------------------------------- perceive
    def observe(self, actor, action, extra=None):
        extra = extra or {}
        now = time.time()
        with self._lock:
            weight = RISK_WEIGHTS.get(action, 5)
            self._add(actor, action, weight, SIGNALS.get(action, (action, action))[1], now)

            if action == "failed_login":
                self.login_attempts[actor] = self.login_attempts.get(actor, 0) + 1
                n = self.login_attempts[actor]

                if "known_user" in extra:
                    self.context[actor] = {"known_user": bool(extra["known_user"])}

                # Extra penalty for repeated failed logins (unchanged behaviour)
                if n >= 2:
                    self._add(actor, "repeated_failures", RISK_WEIGHTS["repeated_failures"],
                              f"{n} failed logins so far", now)

                # Failed logins in quick succession
                last = self._last_fail.get(actor)
                if last is not None and (now - last) <= RAPID_WINDOW:
                    gap = now - last
                    self._add(actor, "rapid_login_attempts", RISK_WEIGHTS["rapid_login_attempts"],
                              f"Failed again only {gap:.0f}s after the previous attempt", now)
                self._last_fail[actor] = now

                # Bot-like client
                fp = extra.get("fp") or {}
                if fp.get("is_bot"):
                    self._add(actor, "automated_client", RISK_WEIGHTS["automated_client"],
                              f"User-Agent flagged as bot: {fp.get('user_agent', '?')[:60]}", now)

            score = self.risk_scores[actor]

            if actor in self.trapped_actors:
                return True

            if score >= REDIRECT_THRESHOLD:
                self._decide_to_trap(actor, score, now)
                return True

            level = "SUSPICIOUS" if weight > 0 else "INFO"
            self.logger.log(actor, action, f"risk_score={score}", risk_level=level)
            return False

    # ----------------------------------------------------------------- decide
    def _decide_to_trap(self, actor, score, now=None):
        self.trapped_actors.add(actor)
        self.trap_time[actor] = now or time.time()
        self.logger.log(
            actor,
            "AGENT DECISION: threshold crossed → redirecting to DECOY",
            f"final_score={score}",
            risk_level="TRAPPED"
        )
        self.logger.save()

    # -------------------------------------------------------------------- act
    def store_fingerprint(self, actor, fp):
        with self._lock:
            self.fingerprints[actor] = fp
        self.logger.log(actor, "FINGERPRINT COLLECTED", str(fp), risk_level="TRAPPED")

    def note_decoy_access(self, actor, resource):
        with self._lock:
            d = self.decoy_access.setdefault(actor, {})
            d[resource] = d.get(resource, 0) + 1

    def is_trapped(self, actor):
        return actor in self.trapped_actors

    def get_risk_report(self):
        return self.risk_scores

    # ---------------------------------------------------------------- explain
    def get_summaries(self):
        with self._lock:
            return {a: self.build_summary(a) for a in list(self.trapped_actors)}

    def build_summary(self, actor):
        """Plain-language case summary: WHY this actor was classified as an illegal user."""
        with self._lock:
            if actor not in self.trapped_actors:
                return None

            events = list(self.events.get(actor, []))
            score = self.risk_scores.get(actor, 0)
            ctx = self.context.get(actor, {})
            fp = self.fingerprints.get(actor, {})
            ip = fp.get("ip", "unknown")

            # --- indicators: group events by signal code
            grouped = {}
            for e in events:
                g = grouped.setdefault(e["code"], {"count": 0, "points": 0, "details": []})
                g["count"] += 1
                g["points"] += e["points"]
                g["details"].append(e["reason"])
            indicators = []
            for code, g in grouped.items():
                title, base = SIGNALS.get(code, (code, code))
                detail = base if g["count"] == 1 else f"{base} (×{g['count']})"
                if code in ("rapid_login_attempts", "automated_client", "repeated_failures"):
                    detail = g["details"][-1]
                indicators.append({"title": title, "detail": detail,
                                   "points": g["points"], "count": g["count"]})
            indicators.sort(key=lambda i: -i["points"])

            # --- observations that didn't score points but support the verdict
            observations = []
            if "known_user" in ctx:
                if ctx["known_user"]:
                    observations.append(
                        f"'{actor}' is a REAL account, but the password was wrong: consistent with password guessing.")
                else:
                    observations.append(
                        f"'{actor}' is NOT a registered account: consistent with guessing or account enumeration.")
            if fp.get("os") or fp.get("browser"):
                observations.append(f"Source device: {fp.get('os', '?')} / {fp.get('browser', '?')}.")

            # --- timeline
            timeline = [{"time": e["clock"], "label": e["reason"] if e["code"] not in SIGNALS
                         else f"{SIGNALS[e['code']][0]}: {e['reason']}",
                         "points": e["points"], "total": e["total"]} for e in events]

            # --- narrative
            fails = self.login_attempts.get(actor, 0)
            fail_events = [e for e in events if e["code"] == "failed_login"]
            first_t = fail_events[0]["t"] if fail_events else (events[0]["t"] if events else time.time())
            trap_t = self.trap_time.get(actor, first_t)
            dur = max(0.0, trap_t - first_t)
            dur_text = "under a second" if dur < 1 else f"{dur:.0f} seconds"

            parts = [f"The agent started tracking '{actor}' at {_clock(first_t)}. "
                     f"Within {dur_text} it saw {fails} failed login attempt{'s' if fails != 1 else ''}."]
            rapid = [e for e in events if e["code"] == "rapid_login_attempts"]
            if rapid:
                parts.append("The attempts came in rapid succession, a pattern typical of scripted "
                             "password guessing rather than a person who simply mistyped.")
            if "known_user" in ctx:
                parts.append("They targeted a real account with the wrong password, which points to password guessing."
                             if ctx["known_user"] else
                             "The username does not belong to any registered account, which points to guessing or account enumeration.")
            if grouped.get("automated_client"):
                parts.append("The browser fingerprint also looks automated.")
            parts.append(f"Each signal added points to a running risk score. It reached {score} and crossed the "
                         f"autonomous redirect threshold of {REDIRECT_THRESHOLD}, so at {_clock(trap_t)} the agent "
                         f"silently moved the session into the decoy environment, with no human approval.")
            access = self.decoy_access.get(actor, {})
            if access:
                parts.append("Since then the intruder has opened " + ", ".join(sorted(access)) +
                             ". All of it is fabricated data.")
            else:
                parts.append("Nothing inside the decoy has been opened yet.")

            # --- recommendations
            recs = []
            note = ""
            try:
                a = ipaddress.ip_address(ip)
                if a.is_loopback or a.is_private:
                    note = " (local/private address, likely your own demo traffic)"
            except ValueError:
                pass
            if ip != "unknown":
                recs.append(f"Block {ip} at the firewall or add it to a watchlist{note}.")
            if ctx.get("known_user"):
                recs.append(f"Rotate the password for account '{actor}' and review its other login history.")
            recs.append("Keep the activity log as evidence (saved to trap_activity_log.json).")
            recs.append("Check the Penetration section to see which services the source machine exposes.")

            return {
                "actor": actor,
                "headline": f"'{actor}' confirmed as an illegal user: risk {score} crossed the threshold of {REDIRECT_THRESHOLD}",
                "score": score,
                "threshold": REDIRECT_THRESHOLD,
                "narrative": " ".join(parts),
                "indicators": indicators,
                "observations": observations,
                "timeline": timeline,
                "decoy_activity": [{"resource": r, "count": c} for r, c in sorted(access.items())],
                "recommendations": recs,
            }
