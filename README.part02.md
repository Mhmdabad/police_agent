### Authorising Gmail, once

```bash
python -m cop_agent.infra.authorize
```

See [`docs/GMAIL_SETUP.md`](docs/GMAIL_SETUP.md). A Testing-mode refresh token
expires after seven days; re-run this if the agent has been idle a week.

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
