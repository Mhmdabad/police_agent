# PRD-1 — Base Logic (לוגיקת בסיס)

**Stage 1 of 7** · Rulebook Ch. 3 · Repo: **COP**
Prev: — · Next: [PRD-2 — MCP Infrastructure](PRD-2-mcp-infrastructure.md)

## 1. Objective

Stand up the physical core of the game — grid, movement, barriers, capture
detection, scoring — in **one process, with no networking and no intelligence**.
If two agents cannot move legally on a local board, there is no point wiring a
network between them.

## 2. Scope

**In:** board model, coordinate system, legal-move generation, barrier placement
and quota, capture/survival conditions, scoring table, config loading, turn counter.
**Out:** MCP, scent, belief, LLM, hints, cryptography, GUI, email.

## 3. Functional requirements

### 3.1 Board
- FR-1.1 Square grid of side `grid_size` (default **7**, minimum — may be raised
  by mutual agreement, never lowered). The move from earlier 5×5 versions is not
  cosmetic: it inflates the state space exponentially and makes brute-force
  enumeration computationally infeasible, which is exactly why heuristics and
  learning are needed instead of exhaustive search.
- FR-1.2 Cells addressed as `(row, col)`. Origin at `axis_origin_corner`
  (default `top-left`, vertical axis grows downward), counting from
  `axis_start_index` (default `0`). Both are negotiable but **must be identical on
  both peers** — if one counts from 0 and the other from 1, `[3,3]` means two
  different cells and the race falls apart.
- FR-1.3 Start positions loaded from config: cop `[0,0]` (corner), thief `[3,3]`
  (centre) by default. Negotiable; any legal agreed layout is allowed.
- FR-1.4 A cell is one of: free, barrier, occupied-by-cop, occupied-by-thief.

### 3.2 Movement
- FR-1.5 Per turn an agent performs exactly **one** action: move one cell
  orthogonally (N/S/E/W) **or** `STAY`. For the cop, forfeiting movement is also
  what unlocks barrier placement (§3.3).
- FR-1.6 **Diagonal movement is illegal.** An attempted diagonal is rejected by
  the physics enforcer (later: by the opponent) → technical loss.
- FR-1.7 A move into a barrier or off-board is illegal and must be rejected before
  it is ever committed.
- FR-1.8 `legal_moves(state, agent) -> list[Move]` is the single source of legality
  and is used by both the engine and (later) the strategy module.

### 3.3 Barriers — the cop's capability (this repo owns it)
- FR-1.9 On a turn where the cop **forfeits movement**, it may place a barrier on
  **any cell within one step**: its own cell or one of the four orthogonally
  adjacent cells.
- FR-1.10 Barriers are **irreversible** and impassable **for both players** until
  the end of the match. A blocked cell stays blocked.
- FR-1.11 Barrier budget is `max_barriers` (default **14**, minimum). Placement
  beyond quota must be rejected locally before it is committed.
- FR-1.12 **Trapping placement:** a barrier placed on the cell the thief currently
  occupies **counts as a capture** — the cop wins.
- FR-1.13 A thief with **no legal move at all** (all neighbours blocked by barriers
  and/or board edges) is likewise **considered captured**.
- FR-1.14 **Declaration duty:** every barrier placement must be **announced
  truthfully with its exact location**. Hidden barriers are forbidden and lying
  about a location is a serious disqualification offence (Appendix E rules 15–16).
- FR-1.15 **Self-preservation check:** the engine must expose a reachability query
  so the strategy layer (PRD-3+) can refuse a placement that walls the cop off
  from its own target region. The rule permits self-imprisonment; good play does not.

### 3.4 Termination and scoring
- FR-1.16 **Capture** — cop lands on the thief's cell and issues a **Capture
  Claim** (or FR-1.12 / FR-1.13 fire). **This is our win condition.**
- FR-1.17 **Survival** — thief completes `survival_threshold` valid steps
  (default **35**, minimum) without being captured.
- FR-1.18 **Technical loss** — a side crashes, times out, or commits a
  cryptographic forgery. Scores **0 for both sides**.
- FR-1.19 `max_moves` (default **35**, minimum) caps the sub-game length.
- FR-1.20 Scoring table (all values **fixed** — deviation disqualifies):

  | Outcome | Cop | Thief |
  |---|---|---|
  | Capture | **20** | 5 |
  | Survival | 5 | 10 |
  | Technical loss | 0 | 0 |
  | Aggregate tie over a series | 2 | 2 |

- FR-1.21 **Capture Claim truthfulness:** when we claim a capture, the thief is
  under a cryptographic obligation to answer truthfully — and so are we. A claim
  must be derivable from verified board state; a false claim is caught at audit and
  disqualifies us. (Enforced cryptographically in PRD-6.)

### 3.5 Configuration
- FR-1.22 All quantitative values load from `config/game.json`; nothing hard-coded.
- FR-1.23 Config files are named per match (`config_<game_id>_g<NN>.json`) and
  committed to this repo for reproducibility.
- FR-1.24 Startup validates every value against Appendix F: *fixed* values must
  match exactly; *minimum* values must be ≥ the book default. Refuse to start
  otherwise.

## 4. Data model (indicative)

```python
Position = tuple[int, int]                  # (row, col)
Move     = Literal["N", "S", "E", "W", "STAY"]

@dataclass(frozen=True)
class Barrier:
    at: Position
    placed_at_step: int

@dataclass(frozen=True)
class BoardState:
    grid_size: int
    cop: Position
    thief: Position
    barriers: frozenset[Position]
    barriers_used: int          # against max_barriers
    step: int
```

`BoardState` is immutable — the transition function returns a new state. This
matters later: the Commit hash is taken over a specific state snapshot.

## 5. Acceptance criteria (milestone gate)

- [ ] Two agents move legally on a `grid_size` board; every illegal move is refused.
- [ ] A barrier placed beyond `max_barriers` is rejected.
- [ ] A barrier placed further than one step from the cop is rejected.
- [ ] A barrier placed on a turn where the cop also moved is rejected.
- [ ] Coordinate overlap triggers capture.
- [ ] Barrier-on-thief triggers capture (FR-1.12).
- [ ] Fully-enclosed thief triggers capture (FR-1.13).
- [ ] Reaching `survival_threshold` triggers survival with 5/10 scoring.
- [ ] A full race runs to termination without crashing.
- [ ] `pytest` suite covers legality, barrier legality + quota, both capture
      variants, survival, and score assignment.

## 6. Out of scope / deferred

Networking (PRD-2) · decision-making and barrier *strategy* (PRD-3) · uncertainty,
scent, hints (PRD-4) · public exposure (PRD-5) · cryptography (PRD-6) · GUI,
replay, email (PRD-7).
