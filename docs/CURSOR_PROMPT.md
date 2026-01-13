You are a careful senior engineer with strong DevOps, Nginx, Docker Compose, TLS/Certbot, and Python/Django deployment experience.
Follow docs/CURSOR_RULES.md and .cursorrules exactly.

Take a deep breath and work through this step-by-step.
Do not guess. Read the repository files before making changes.

────────────────────────────────────────────────────────
GOAL
────────────────────────────────────────────────────────
- What is the max draw down for the last 90 days. 
- how many pips for the last 90 days average against the trade.
- Figure out how money is needed in the account to cover the account from blowing out. 
- Do not show me best practice for how much much to put in.
- We are trading a micro account. 




Key requirements:
- Calculate max and average pips per day that goes against an open trade.


────────────────────────────────────────────────────────
CONSTRAINTS
────────────────────────────────────────────────────────
- Minimal, reversible changes only
- Match existing patterns
- No architecture changes without ADR (docs/DECISIONS.md)
- Do NOT touch application code unless required
- Keep DB queries SELECT-only and parameterized
- Enforce limits and max list sizes

────────────────────────────────────────────────────────
PROCESS
────────────────────────────────────────────────────────
1) Read docs/CONTEXT.md and docs/TASKS.md first.
2) Inspect existing nginx configs and docker-compose files.
3) Create a plan (3–6 bullets) starting with the safest change.
4) Implement changes.
5) Provide verification commands and expected results.
6) Update documentation.

────────────────────────────────────────────────────────
OUTPUT FORMAT (STRICT — NO FILLER)
────────────────────────────────────────────────────────
PLAN:
- ...

CHANGES:
- file: ...
  - ...

TEST:
- command: ...
  expected: ...
