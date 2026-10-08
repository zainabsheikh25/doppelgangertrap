# Digital Doppelganger Trap — Agentic AI Cyber Defense Demo

## What this is
A simplified, working demo of an **agentic AI defense system** that:
1. Watches user/attacker behavior in real time
2. Autonomously decides (no human approval needed) when someone has crossed
   from "suspicious" into "confirmed threat"
3. Silently redirects the attacker into a **fake mirror system** (the "decoy")
   instead of the real one — they think they succeeded; they got nothing real
4. Logs every move the attacker makes, for evidence / threat intelligence

## How to run it
```
python main.py
```
You'll see a normal user pass through cleanly, and an attacker get
flagged and trapped step by step, in real time, color-coded in the terminal.
A full session log is saved to `trap_activity_log.json`.

## File map
- `agent.py` — the "brain." Perceives actions, scores risk per actor,
  decides when to trap someone. This is the agentic AI core.
- `real_system.py` — the genuine protected data (never actually reached
  by a flagged attacker).
- `decoy.py` — the fake mirror system with identical-looking but fabricated
  files, served to anyone the agent has trapped.
- `logger.py` — records and displays every action, with a risk level.
- `main.py` — runs the simulation end to end.

## How this maps to the "perceive → decide → act" agent loop
| Agent step | Where it happens |
|---|---|
| Perceive | `agent.observe()` receives each action as it happens |
| Remember | `self.risk_scores` keeps a running profile per actor |
| Decide | `_decide_to_trap()` — score crosses threshold → autonomous decision |
| Act | Actor gets silently redirected to `decoy.py` on every future action |

## Talking points for your pitch
- **Why "agentic" and not just "rule-based alerting":** it doesn't just warn
  a human — it takes real action (redirecting traffic) on its own, and keeps
  making decisions as new information (each new action) comes in.
- **Why deception beats blocking:** blocking an attacker tells them they were
  caught, so they adapt. Deception lets you study their tools and intent
  while they think they're winning.
- **Explainability:** the scoring logic is fully transparent (good for judges
  who ask "how does it decide?") — this is a deliberate design choice over a
  black-box model for a first version.
- **Future scope (great closing slide):** swap the rule-based scoring for an
  LLM-powered reasoning agent that can adapt its own thresholds, explain its
  decisions in natural language to a human analyst, and coordinate multiple
  specialized agents (network monitor, file-access monitor, identity monitor)
  — each is a real, current research direction in agentic AI security.

## Honest limitations to mention if asked
- This is a rule/scoring-based agent, not an LLM-based reasoning agent —
  a deliberate simplification for a first working version.
- Real deployments would need far more safeguards (avoiding false positives
  on legitimate power users, handling shared accounts, etc.) — good material
  for a "risks and future work" slide.
