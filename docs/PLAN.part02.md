   the course never taught RL and a winning agent can be built without it.
   A high discount factor γ encourages strategic patience, e.g. building a barrier
   trap over many turns.

**Our plan: start with (1), graduate to (2).** Stage 3 ships a pure
belief + Manhattan policy that *minimises* distance to `argmax b(s)`. Stage 4+
upgrades it to a cop-specific pursuit-and-containment policy:

- **Pursuit:** minimise Manhattan distance to the highest-belief cell; break ties
  by which successor keeps more of the belief mass inside our reachable region.
- **Containment (the real edge):** score candidate barrier placements by how much
  they **reduce the thief's flood-fill escape area**, weighted by belief mass in
  the region being sealed.
- **Self-preservation constraint:** never place a barrier that reduces *our own*
  reachable area below the belief mass we still need to reach. Reject any
  placement that disconnects us from `argmax b(s)`.
- **Budget curve:** spend barriers slowly while belief is diffuse; spend
  aggressively once belief concentrates into one focus and the thief is near an
  edge. Hold a reserve of 2–3 for the closing squeeze.
- **Movement forfeit cost:** placing a barrier costs a turn of pursuit. Only place
  when `Δ(thief escape area) > Δ(distance closed by moving)` under the current
  belief.

RL, if we get there at all, is a stage-8 stretch goal and will be documented with
learning curves in the README (mandatory if used — §9.4.2 item 4).

---

## 4. Scent (stigmergy) — the un-fakeable channel

Every time an agent moves or stays, it emits a **5×5 scent field** centred on its
cell with intensity `0.9` at the centre, falling off radially. After every *full*
turn (cop + thief both moved) all scent decays:

```
τ_ij(t+1) = max(0, (1 − ρ)·τ_ij(t) + Δτ_ij)      with ρ = 0.10
```

Each side reads **the opponent's** scent field, never its own. With ρ = 0.10 a
single deposit stays above half-peak for roughly six to seven turns — long enough
to be tactically useful, short enough not to saturate the board.

**The cop's core exploit:** the thief's trail cannot be forged, so a hint that
contradicts the measured field is a detectable lie *and* a bearing. The book's
worked example: the thief says "I moved north"; a fresh northern trail would read
≈ (1−ρ)·0.9 ≈ 0.81, but the north measures **0.00** while all the scent mass sits
in the south-east. The cop concludes with high confidence that the thief is lying,
lowers the hint reliability coefficient, re-weights belief toward the south-east
and re-aims. The thief's manipulation becomes a double-edged sword.

**The mirror risk:** the thief runs the same procedure on *our* trail and *our*
hints. Our deception must stay consistent with the physics we emit.

Before a series starts, both teams must exchange the full emission/decay model
**with a concrete numeric example** and lock the agreement cryptographically
(SHA-256 of the formula + example). Sharing the actual scent-engine code with the
opponent is explicitly permitted and recommended (Rulebook §4.5).

---

## 5. Integrity — Commit-Reveal over SHA-256

Four mandatory phases per step:

1. **Commit** — send only
   `H = SHA256(State ‖ Move ‖ Intent ‖ Nonce)`.
   Serialisation is **canonical JSON** (`sort_keys=True`, `separators=(",",":")`)
   so both peers hash byte-identical input. `Intent` is a flag declaring in
   advance whether the accompanying hint is `truth` or `lie` — you cannot claim
   afterwards that you "meant" to lie. `Nonce` is `secrets.token_hex(16)`
   (never `random`).
2. **Acknowledge** — opponent confirms it is locked on our commitment.
3. **Reveal** — send `Move` + hint. **The nonce stays secret.**
4. **Final Reveal / Audit** — at end of match, all nonces are revealed; each side
   recomputes the other's hashes.

Any mismatch is **proof of tampering** — no interpretation, no statistical doubt.
The cheating team takes a **technical loss (0 points)** regardless of the board.

For the cop specifically: a **Capture Claim** places the thief under a
cryptographic obligation to answer truthfully — but it also binds us. Barrier
placements and the claim itself are sealed in the log and re-verified at audit;
a false capture claim carries **immediate disqualification with no appeal**
(Appendix E rules 21–22).

**Step-0** (before move 1): both sides publish a signed hardware declaration —
OS, CPU cores/frequency, RAM, GPU/VRAM, LLM model name — plus code version, team
name, sub-game number, and **the exact GitHub commit hash being played**. Code may
change between matches; the commit hash must be re-declared every match so the
grader can reproduce the version that actually competed.

---

## 6. Configuration — the shared constitution

Two files, two purposes (Appendix B):

| File | Format | Scope | Signed? |
|---|---|---|---|
| `config/game.json` | JSON | **Shared**, byte-identical on both peers: board, movement, scoring, pheromones, network/league, rate limiter | **Yes** (`config_sha256`) |
| `config/police/game.toml` | TOML | **Private**: my port, opponent URL, strategy class, LLM/trash-talk provider, email target, team identity | No |

Decision test: *"must the opponent agree to this value, or rely on it?"* → JSON.
Otherwise → TOML. When both exist, **JSON overrides TOML** for any shared key, so a
private file can never weaken a signed condition.

The negotiated contract is a **floor, not a ceiling**: parameters marked
*minimum* may be raised by mutual agreement but never lowered; *fixed* parameters
may not change at all; *negotiable* parameters are free. Any deviation from a
*fixed* value disqualifies the team.

### Binding defaults (Appendix F — single source of truth)

```jsonc
{
  "schema_version": "1.2",
  "agreed_between": ["group-a", "group-b"],
  "board_and_agents": {
    "grid_size": 7,               // minimum
    "num_agents": 2,              // fixed
    "thief_start": [3, 3],        // negotiable
    "cop_start": [0, 0],          // negotiable
    "axis_origin_corner": "top-left",
    "axis_start_index": 0
  },
  "world": { "map_area": "New York", "hint_max_words": 15 },
  "movement_and_barriers": {
    "move_set": ["N","S","E","W","STAY"],   // fixed — no diagonals
    "max_barriers": 14,           // minimum — OUR budget
    "max_moves": 35,              // minimum
    "survival_threshold": 35      // minimum — the clock we race
  },
  "scoring": {                     // all fixed
    "capture_cop": 20, "capture_thief": 5,
    "survival_cop": 5, "survival_thief": 10,
    "tie_score": 2, "technical_loss": 0
  },
  "pheromones": {                  // all fixed
    "pheromone_center_intensity": 0.9,
    "pheromone_decay": 0.10,
