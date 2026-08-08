# COP Agent (שוטר) — Distributed Cops-and-Robbers over a Peer-to-Peer Network

[![CI](https://github.com/Mhmdabad/police_agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Mhmdabad/police_agent/actions/workflows/ci.yml)

Final project — **Orchestration of AI Agents**, Computer Science Department,
University of Haifa, 2026. Rulebook: *Distributed Cops-and-Robbers over a
Peer-to-Peer Network*, book version 3.0.0, Dr. Yoram Reuven Segal.

> **Companion repository — THIEF agent: <https://github.com/Mhmdabad/theif_agent>**
>
> This team submits two repositories. This one holds the **COP**; the link above
> holds the **THIEF**. The two agents run as completely separate processes under
> separate configuration directories and share no state whatsoever.

---

## Contents

- [What this is](#what-this-is)
- [Status](#status)
- [Running it](#running-it)
- [Repository layout](#repository-layout)
- **Academic report**
  - [1. The Dec-POMDP model](#1-the-dec-pomdp-model)
  - [2. FastMCP orchestration dilemmas](#2-fastmcp-orchestration-dilemmas)
  - [3. Strategies implemented](#3-strategies-implemented)
  - [4. Learning curves](#4-learning-curves)
  - [5. Screenshots](#5-screenshots)
  - [6. Companion repository](#6-companion-repository)
- [Documented rulebook contradictions](#documented-rulebook-contradictions)
- [Team](#team)

---

## What this is

A cop chases a thief on a discrete grid with **no central server and no
referee**. Neither agent observes the true world state: each maintains a belief
over its opponent's position, built from a decaying **scent field** that cannot
be faked and a **verbal hint** that may be a deliberate lie.

Each agent is simultaneously an MCP server and an MCP client over **FastMCP**,
exposed to the public internet through a tunnel. Integrity is enforced by
**Commit-Reveal over SHA-256** rather than by an authority: every move is sealed
before it is disclosed, and the full match log is mutually audited afterwards.

This repository implements the **COP** — the side that pursues, places barriers,
and claims capture.

## Status

Stages 0–7 are complete: both agents run, expose the four MCP tools over a
tunnel, play a full Commit-Reveal match against each other, audit the
opponent's every step, and write the four mandatory artefacts. What remains is
league play and submission — matches against other teams, screenshots, and the
Moodle paperwork.

Progress is tracked as one GitHub issue per task, labelled by build stage
(`stage-0` … `stage-7`, `league`, `submission`, `final-checklist`).

| Stage | Scope | State |
| --- | --- | --- |
| 0 | Repository setup | complete |
| 1 | Base logic | complete |
| 2 | FastMCP infrastructure | complete |
| 3 | Strategy module | complete |
| 4 | Language and scent | complete |
| 5 | Cloud exposure | complete |
| 6 | Cryptography | complete |
| 7 | Reporting, GUI, replay | complete |
| — | League play and submission | in progress |

Every merge is gated on `ruff`, `ruff format`, `mypy --strict`, a 100 %-covered
test suite, and a cross-repository drift check that fails if a module shared
with the companion agent has diverged.

**Known limits, stated rather than discovered.** The Step-0 declaration reads
`"unsigned"` until the course issues the signing key. The verbal layer runs in
zero-token `template` mode by default, so `total_tokens` is 0 until the
`claude_api` provider is enabled. Neither is a defect; both are choices with a
reason, and the reasons are in [`docs/SECRETS.md`](docs/SECRETS.md) and
[`docs/prd/PRD-4-language-and-scent.md`](docs/prd/PRD-4-language-and-scent.md).

Planning documents: [`docs/PLAN.md`](docs/PLAN.md),
[`docs/TODO.md`](docs/TODO.md), [`docs/prd/`](docs/prd/README.md).
A transcription of the rulebook is in [`project-book/`](project-book/README.md).

## Running it

```bash
uv sync
```

### Serve — answer an opponent

```bash
python -m cop_agent serve
```

Binds `0.0.0.0` and exposes the four MCP tools. Runs happily without a tunnel,
because local development must not be conditional on ngrok.

### Check — before you commit to a match

```bash
PUBLIC_URL=https://ours.ngrok.io OPPONENT_URL=https://theirs.ngrok.io/mcp \
    python -m cop_agent check
```

Prints the port, the address we would advertise, the opponent, and the tool
names — and binds nothing. If it says *not publicly reachable*, **stop**:
announcing a loopback address means every call the opponent makes times out,
and a technical loss scores zero for *both* sides.

### Play — a whole match

```bash
PUBLIC_URL=https://ours.ngrok.io OPPONENT_URL=https://theirs.ngrok.io/mcp \
    python -m cop_agent play --game-id AGREED_ID --out artefacts
```

Handshake → agree the config digest → play the sub-games → audit the opponent →
write `declaration_`, `config_`, `log_` and `result_`. The `game_id` is agreed
with the opponent beforehand: both sides name their files from it.

**It sends nothing.** FR-7.16 requires both teams to agree the result before
either reports it, so the report is written with `result_agreed_with_opponent`
false and mailing it is a separate, deliberate act.

### The two windows

```bash
python -m cop_agent.ui.app live
python -m cop_agent.ui.app replay artefacts/log_<game_id>_g01.json
```

The live board never receives the opponent's true cell — `render()` has no
parameter for it. The Replay App stamps the log `Verified OK` or `TAMPERED`,
computed over the whole file rather than the step on screen.
