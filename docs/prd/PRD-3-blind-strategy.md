# PRD-3 — "Blind" Strategy Module (מודול אסטרטגיה עיוור)

**Stage 3 of 7** · Rulebook Ch. 6 · Repo: **COP**
Prev: [PRD-2](PRD-2-mcp-infrastructure.md) · Next: [PRD-4 — Language & Scent](PRD-4-language-and-scent.md)

## 1. Objective

Wire in a first decision-making module that operates in a world of **complete and
accurate information** — the thief's true position is known. "Blind" here means
blind to *uncertainty*: no scent, no natural language, no deception yet. The point
is to isolate the correctness of the decision core — pursuit **and** barrier
management — before the fog is switched on.

## 2. Scope

**In:** strategy module interface and its exact insertion point, pursuit policy v1,
barrier placement policy v1, legality guard, deterministic reproducibility.
**Out:** belief maps and Bayes (PRD-4), hints and LLM (PRD-4), crypto (PRD-6).

## 3. Functional requirements

### 3.1 Module boundary
- FR-3.1 The strategy module is a **separate module** plugged into the
  `PeerRuntime` at exactly one point: **immediately after decoding the incoming
  hint, and before packing the outgoing Commit.** All of the agent's intelligence
  lives between those two points.
- FR-3.2 Interface follows the reference contract so it can be swapped from
  config: a class inheriting `BrainBase` / `PoliceBrain` that overrides
  `_pick_move` **and `_decide_move`** — the latter is where the cop chooses
  *whether* to place a barrier and *where*. Selected in `config/police/game.toml`:

  ```toml
  [strategy]
  police_class = "my_team.strategy:MyPoliceBrain"   # package.module:Class
  ```
  Leaving the section empty runs the shipped combined heuristic brain.
- FR-3.3 The module returns **only a legal action** — move or barrier placement —
  validated against PRD-1 rules before it can be committed.

### 3.2 Policy v1 — pursuit under full information
- FR-3.4 Compute Manhattan distance to the target:
  `D = |r_cop − r_target| + |c_cop − c_target|`. Manhattan is the admissible
  estimate for orthogonal grid movement with no diagonals.
- FR-3.5 Choose the legal move that **minimises** `D`.

  Worked example from the book: cop at `(2,2)`, target at `(5,5)` ⇒ `D = 6`.
  East `(3,2)` gives `D = 5`, north `(2,3)` also `D = 5`, west `(1,2)` gives
  `D = 7`. The agent picks east or north — both reduce `D` by one step — and breaks
  the tie by the secondary criterion below.
- FR-3.6 **Tie-break by containment value**, not arbitrarily: prefer the successor
  that reduces the thief's flood-fill escape area more, or that keeps the thief
  closer to a board edge / existing barrier chain.
- FR-3.7 Never step into a cell that leaves us with fewer reachable cells than the
  region we still need to cover.

### 3.3 Policy v1 — barrier management
- FR-3.8 Barrier placement costs a full turn of pursuit (movement is forfeited).
  Place only when
  `Δ(thief escape area) > Δ(distance closed by the best available move)`
  under the current model of the thief's position.
- FR-3.9 Score each candidate cell (own cell + 4 orthogonal neighbours) by:
  1. reduction in the thief's reachable free area (flood fill),
  2. whether it completes or extends an existing barrier chain toward an edge,
  3. **penalty** if it disconnects the cop from the target region.
- FR-3.10 **Self-preservation constraint (hard):** reject any placement that walls
  the cop off from its target, or that reduces our own reachable area below what we
  need. A greedy barrier can imprison the cop behind a wall of its own making, or
  open the thief a fresh escape corridor.
- FR-3.11 **Budget curve:** with `max_barriers` = 14, spend slowly while the
  target is uncertain or far; spend aggressively when the thief is cornered.
  Hold a reserve of 2–3 barriers for the closing squeeze.
- FR-3.12 Prefer placements that create the **trapping win** (FR-1.12: barrier on
  the thief's own cell) or the **enclosure win** (FR-1.13: thief left with no legal
  move) when either is one placement away.
- FR-3.13 Every placement emits a truthful `declare_barrier` (PRD-2 FR-2.8).
  There is no path that places without declaring.

### 3.4 Alternative policies (documented choice)
The book treats three routes as **equal citizens**; in all three the spatial
decision stays algorithmic:

1. **Pure heuristics** — Bayesian belief + Manhattan. *Reference default; our
   starting point.*
2. **Your own heuristic algorithm** — belief + scent + barrier exploitation +
   lookahead (minimax / expectimax against the opponent's belief). *Our target.*
3. **Reinforcement learning** — Q-Learning with the Bellman update and
   ε-greedy exploration. **Optional**; RL was never taught in the course and a
   strong agent needs no RL at all.

   ```
   Q(s,a) ← Q(s,a) + α [ r + γ·max_a' Q(s',a') − Q(s,a) ]
   ```
   A high discount factor γ rewards **strategic patience** — for instance building
   a barrier trap over many turns rather than chasing the immediate reward.
   ε-greedy exploration prevents the pursuit from locking into a repeating loop.
   If used, learning curves become a **mandatory** README section.

- FR-3.14 Whichever route is chosen, it must be stated and justified in the README
  academic report.

### 3.5 Hard constraint — the LLM does not move the agent
- FR-3.15 The move and barrier decisions are **always** computed in Python. LLMs
  hallucinate in Cartesian space — confusing directions, distances and coordinates
  — and will confidently return an illegal, wall-colliding or self-destructive
  action.
- FR-3.16 A single documented exception exists: if **both teams explicitly and
  mutually agree in pre-match negotiation**, an LLM-based move tactic is permitted.
  Even then the local algorithm must still enforce legality and reject any illegal
  suggestion, and the hallucination risk is on the team that chose it. One side may
  **not** adopt this unilaterally. Our default remains fully algorithmic.

### 3.6 Determinism
- FR-3.17 Given identical state and identical config, the policy returns an
  identical action. Any stochastic element (e.g. ε-greedy) is seeded and the seed
  is logged, so a match can be replayed exactly.

## 4. Acceptance criteria (milestone gate)

- [ ] Given a known target position, the agent computes and executes the shortest
      pursuit path with **no manual intervention**.
- [ ] The module never returns an illegal move or an illegal placement (property
      test over random boards).
- [ ] Swapping the brain class via `config/police/game.toml` changes behaviour
      without touching runtime code.
- [ ] The self-preservation constraint is exercised: a placement that would wall
      the cop off is rejected (regression test with a hand-built board).
- [ ] A one-placement-away trapping win is taken when available.
- [ ] Barrier budget never exceeds `max_barriers`.
- [ ] Same state + same seed ⇒ same action, across runs.

## 5. Out of scope / deferred

Probabilistic belief and Bayes updates (PRD-4) · scent reading (PRD-4) · hint
generation and bluff classification (PRD-4) · commitment of the chosen action
(PRD-6) · heatmap visualisation (PRD-7).
