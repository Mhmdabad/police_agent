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

Under development. Progress is tracked as one GitHub issue per task, labelled by
build stage (`stage-0` … `stage-7`, `league`, `submission`, `final-checklist`).

| Stage | Scope | State |
| --- | --- | --- |
| 0 | Repository setup | in progress |
| 1 | Base logic | not started |
| 2 | FastMCP infrastructure | not started |
| 3 | Strategy module | not started |
| 4 | Language and scent | not started |
| 5 | Cloud exposure | not started |
| 6 | Cryptography | not started |
| 7 | Reporting, GUI, replay | not started |

Planning documents: [`docs/PLAN.md`](docs/PLAN.md),
[`docs/TODO.md`](docs/TODO.md), [`docs/prd/`](docs/prd/README.md).
A transcription of the rulebook is in [`project-book/`](project-book/README.md).

## Running it

```bash
uv sync
```

<!-- TODO: expand once the peer entry point exists (PRD-2). Target shape:
     uv run python -m cop_agent peer --role police
     uv run python -m cop_agent replay --log logs/police_match.json          -->

Quality gates run on every push and pull request: `ruff check`, `ruff format`,
`mypy`, and `pytest` with a coverage floor defined in `pyproject.toml`.

## Repository layout

```
config/        shared signed game.json + private police/game.toml
docs/          PLAN, seven PRDs, TODO
project-book/  Markdown transcription of the course rulebook
src/cop_agent/ the agent
tests/         pytest suite
```

---

# Academic report

> The six sections below are mandatory (Rulebook §9.4.2). They are stubbed here
> and filled in as the corresponding stage completes; each carries a note saying
> what belongs in it and which stage produces the material.

## 1. The Dec-POMDP model

<!-- Required: a scientific description of the formalism adopted for this race —
     the state space, the observation function available to each agent, and the
     structure of the uncertainty. Specific to our implementation, not generic
     textbook prose. Source: Rulebook ch. 1. Produced by: PRD-1, PRD-4.        -->

*To be written — see PRD-1 (state space) and PRD-4 (observations, belief).*

## 2. FastMCP orchestration dilemmas

<!-- Required: the development trade-offs around orchestrating communication
     between two mutually untrusted agents — turn management, handling network
     failures, and the roles of the Gatekeeper and Orchestrator patterns. The
     grader is looking for reasoning and rejected alternatives, not a
     description of the final code. Source: ch. 2, ch. 8. From: PRD-2, PRD-5.  -->

*To be written — see PRD-2 (Orchestrator, state machine, reliability patterns)
and PRD-5 (tunnelling, latency, failure handling).*

## 3. Strategies implemented

<!-- Required: the decision mechanism actually built, and why. The rulebook
     treats three routes as equal-standing: pure heuristics (Manhattan distance
     + Bayesian belief), an LLM-based strategy, or — optionally — Q-Learning.
     What is graded is the quality of the justification. Source: ch. 6.
     Produced by: PRD-3, PRD-4.                                                -->

**Route chosen: our own heuristic algorithm.** Not pure Manhattan-plus-belief,
and not reinforcement learning. The reasoning below is what the implementation
taught us, in the order it taught us, rather than an argument assembled
afterwards.

### The insight the cop is built on

The rulebook's objective for this agent is not *chase the thief*. It is
*shrink the space the thief has*. Appendix D prices capture by the number of
closed sides a cell has: two barriers to seal a corner, three on an edge, four
in the open. Those are not three rules — they are one rule, that a cell needs
four closed sides, with the board supplying the difference for free.

Everything the cop does follows from taking that literally. Herding matters
more than closing, because a thief on an edge is half the price of a thief in
open board, and a barrier that lands on an existing wall or the board edge
finishes work already paid for.

### What the pure-heuristic route gets wrong

**Distance is a poor proxy for progress.** A step that shortens the gap by one
and a step that seals a corridor look identical to a distance metric, and only
one of them is worth a turn.

**It has no way to price a barrier.** Placing forfeits a full turn of pursuit,
and the quota is fourteen across thirty-five turns, so "is this wall good" is
the wrong question; the right one is "is this wall better than the step it
replaces". Nothing in a distance-plus-belief policy can answer that, because
the two sides are not commensurable in it.

We found the sharpest version of this by accident. In the corridor position at
[`test_but_a_barrier_on_the_corridor_beats_the_step`](tests/test_strategy.py),
the best step closes one cell of distance and the best barrier removes
**fourteen** — a third of the board — from the thief's reachable region. A pure
pursuit policy takes the step every time.

### What we built

**A three-axis barrier scorer.** Escape-area reduction by flood fill; chain
progress, counting a sealed neighbour and the board edge as equally closed,
which is where Appendix D's arithmetic comes from; and self-cost.

**Self-preservation as a hard constraint, not a weight.** Two placements are
refused however well they score: one that cuts the cop off from the region it
is hunting, and one that leaves the cop with **no legal move at all**. The
second is the expensive one — a cop that cannot move cannot answer its turn,
and an unanswered turn is a technical loss worth zero to *both* sides. It is
reachable in one step from a corner with two neighbours already sealed, where
the cop's own cell is the only remaining candidate and scores the highest
chain value on the board.

**A spending curve with a reserve.** The value a placement must deliver falls
as belief concentrates, because a barrier against a diffuse belief is a
permanent cost paid for a guess. Three barriers are withheld until the position
is a squeeze the reserve could actually finish — three rather than two, because
two is the *corner* price and a reserve sized for the cheapest case runs out in
every other one. The consequence looks wrong in a log and is deliberate: the
cop stops placing barriers while it still has three.

**An explicit movement-forfeit comparison, logged on both sides.** Escape area
removed against distance the best move would have closed. The two are not the
same unit and the code says so — the exchange rate is a judgement, not a
derivation — but it is a *stated* judgement, so a placement that looks wrong
afterwards can be argued with on its own figures.

**A win check that runs before all of it.** A barrier on the thief's cell or
on its last open side ends the match for twenty points. This has to be checked
first, because the machinery above actively refuses it: the winning cell scores
worst on escape reduction (there is no escape left to reduce) *and* trips the
self-preservation gate (nothing reaches a sealed cell, so we are "disconnected"
from it). Both are correct about what they measure and both are wrong about
what to do, because the match is over.

### Why not reinforcement learning

Four reasons, in descending order of how much each actually decided it.

1. **The sample budget does not exist.** RL needs episodes in the thousands.
   We have at most ten league games against opponents whose policies differ,
   and 200 000 tokens per series. Self-play would train against the one
   opponent we control and will never face.
2. **Determinism is a requirement, not a preference.** A match must replay
   exactly; a learned policy puts the weights into the reproduction, and the
   weights are not in the transcript.
3. **The rulebook makes it costlier.** RL was never taught and is explicitly
   optional, and choosing it makes learning curves a *mandatory* README
   section.
4. **The justification is what is graded**, and every rule above terminates in
   an Appendix D or Appendix F citation. A learned policy can only be described
   statistically.

The seeded RNG is wired and the seed is logged every turn regardless, so an
ε-greedy element would be reproducible from day one. Nothing currently draws
from that stream, and a test asserts so.

## 4. Learning curves

<!-- Required ONLY if reinforcement learning was used, as empirical evidence of
     policy convergence. If no RL was used, say so explicitly — RL is an
     optional tool that the course never taught. Source: ch. 6.                -->

**Not applicable.** Reinforcement learning is not used by this agent, for the
four reasons set out in section 3. Both kinds of turn — relocation and barrier
placement — are deterministic: identical state plus identical config yields an
identical action, verified across processes under four different
`PYTHONHASHSEED` values as well as across runs.

This section is mandatory only where RL was used. It is left in place and
answered explicitly rather than deleted — a missing section and a section that
says "we did not do this, here is why" read very differently to a grader.

## 5. Screenshots

<!-- ABSOLUTE REQUIREMENT (Rulebook §9.4.2 item 5, Appendix C). Two images:
     (a) the Live GUI belief heatmap, evidencing genuine probabilistic inference
         under partial observation;
     (b) the Replay App displaying a green "Verified OK" stamp, evidencing that
         match integrity held.
     Produced by: PRD-7.                                                       -->

*Pending — produced by PRD-7.*

| View | Image |
| --- | --- |
| Live GUI — belief heatmap | *pending* |
| Replay App — `Verified OK` | *pending* |

## 6. Companion repository

**THIEF agent: <https://github.com/Mhmdabad/theif_agent>**

The cross-link is mandatory in both directions: this README points at the thief
repository, and the thief README points back here. The Moodle submission carries
both links; the end-of-match JSON carries four (both teams, both roles).

---

## Documented rulebook contradictions

The rulebook grants academic freedom where it contradicts itself, provided the
report records **where** the contradiction was found, **what** was chosen, and
**why**. Quantitative values remain governed solely by Appendix F.

| # | Where | Choice made | Rationale |
| --- | --- | --- | --- |
| 1 | **Scent falloff shape.** Ch. 4.3 calls the emission a *radial distribution*; the reference implementation in [Appendix D's repository](https://github.com/rmisegal/Game-P2P-Cop-Chase) (`domain/smell.py`) uses **Chebyshev** distance, producing a square terrace whose entire 5×5 border shares one value. | The **PDF's Euclidean Gaussian**, σ = 1.15. Chebyshev is retained as a selectable model so a series against an opponent running the reference code costs a negotiation rather than a code change. | Figure 4 (p. 44) prints the whole field, and two of its numbers settle the shape without any fitting: `(1,2)` and `(2,1)` are **0.14** while `(2,2)` is **0.04**. Under Chebyshev all three are ring 2 and would be equal. The difference is the mechanism, not a detail — ch. 4.3 states the point of spreading at all is that a hill marks *direction* when the exact cell is missed, and a terrace of equal border values carries none. |
| 2 | **Decay rule.** Ch. 4.3 gives `τ(t+1) = max(0, (1−ρ)·τ(t) + Δτ)` — multiplicative. The same reference implementation subtracts: `τ − ρ`. | The **PDF's multiplicative rule**. One turn from 0.9 gives **0.810**, not 0.800. | The book states it four times over: the formula (p. 43), the prose gloss that the trail keeps *90% of its value* each turn (p. 43), the worked lie-detection example computing `(1−ρ)·0.9 ≈ 0.81` (p. 47), and the half-life of six-to-seven turns — true of `0.9ⁿ`, but `0.9 − 0.1n` crosses half at 4.5. Subtraction also decouples lifetime from strength, so a faint *old* trace and a faint *fresh* one become indistinguishable and intensity stops encoding recency. |
| 3 | **Enclosure capture.** Ch. 3 defines it as *"a thief imprisoned with no legal move at all"*, then parenthesises *"(all adjacent cells blocked by barriers and/or board edges)"*. Read literally, the first clause **never fires** — `STAY` survives any encirclement, so a thief always has a legal move. | The **parenthetical**: enclosure is decided over the four **adjacent** cells, and standing still is not an escape. | The literal reading makes the condition unreachable, which cannot be the intent of a rule the book prices at two barriers in a corner and four in the open. The parenthetical is the operative definition and is the only one under which Appendix D's arithmetic holds. |
| 4 | **Agreement key names.** Appendix B names the shared-config keys one way (`grid_size`, `max_barriers`, `pheromone_decay`); the reference repository's negotiation schema uses another (`board_size`, `barriers_max`, `decay_per_step`). | **The reference's key names on the wire, Appendix F's values inside them.** `shared/terms.py` translates between the two. | Key names are a transport detail and must match the opponent's parser or the handshake fails; values are governed by Appendix F, where a *fixed* parameter deviating disqualifies the team. Following the wire for names and the book for values satisfies both, and `test_values_come_from_appendix_f_not_the_key_names` pins the distinction. |

Entries 1, 2 and 4 are divergences between the rulebook and the reference code
published alongside it. In each case the **PDF is treated as authoritative** —
its own header states that the source PDF governs and that Appendix F is the
sole authority for quantitative parameters. The reference implementation is
treated as one more implementation we may have to negotiate against, not as a
standard.

Entries 1 and 2 are both **hash-locked before a series** (see the pre-series
scent lock), so a disagreement surfaces at negotiation rather than mid-match.

## Team

| Field | Value |
| --- | --- |
| Group identifier | `s82kma9e` |

<!-- TODO: member names and student IDs. The group identifier above is the
     8-character code used in every declaration and result JSON, and is what
     the lecturer uses to attribute automated reports to this group.       -->

*Member names to be completed.*

---

<sub>The rulebook and its transcription are © 2026 Dr. Yoram Segal / Gal
Technologies Artificial Intelligence Ltd., reproduced here for authorized
educational coursework.</sub>
