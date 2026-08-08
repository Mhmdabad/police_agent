# TODO — COP Agent (שוטר)

Ordered task list mirroring the seven PRD stages. **A stage is done when the
behaviour has been observed end-to-end — not when "the code is written".** Do not
open stage *n+1* before every gate in stage *n* is ticked.

Legend: `[ ]` open · `[~]` in progress · `[x]` done · **🚪 GATE** = milestone

---

## Stage 0 — Repository setup

- [ ] `README.md`: academic report skeleton + **cross-link to the thief repo**
- [ ] `.gitignore` **before the first commit**: `credentials.json`, `token.json`,
      `*.env`, `config/**/secrets*`, `token*.json`
- [ ] Repo made accessible to the lecturer (public, or private + shared with `rmisegal@gmail.com`)
- [ ] `config/` directory with `game.json` (shared) and `police/game.toml` (private)
- [ ] Python project scaffold (`uv` / `pyproject.toml`), `pytest` wired up
- [ ] Branch-per-feature workflow agreed; merge to main only when stable
- [ ] 8-character group identifier (no spaces) chosen and recorded

---

## Stage 1 — Base Logic → [PRD-1](prd/PRD-1-base-logic.md)

- [ ] `BoardState` model (immutable), `Position`, `Move`, `Barrier` types
- [ ] Coordinate system: origin `top-left`, index from `0`, both configurable
- [ ] `legal_moves()` — N/S/E/W/STAY, **no diagonals**, no barriers, no off-board
- [ ] Transition function returning a new state
- [ ] Barrier placement: only on a turn where movement is forfeited
- [ ] Barrier placement: only on own cell or a 4-orthogonal neighbour
- [ ] Barrier model: irreversible, impassable for both, quota `max_barriers` = 14
- [ ] Reachability / flood-fill query exposed for the strategy layer
- [ ] Capture: coordinate overlap
- [ ] Capture: **barrier placed on the thief's cell** (trapping win)
- [ ] Capture: **thief with no legal move at all** (enclosure win)
- [ ] Survival: `survival_threshold` = 35 valid steps → 5/10 scoring
- [ ] Technical loss → 0/0
- [ ] Scoring table wired from config (capture 20/5, survival 5/10, tie 2)
- [ ] Config loader + **Appendix F validator** (fixed = exact, minimum = ≥)
- [ ] Per-match config naming `config_<game_id>_g<NN>.json`, committed to repo
- [ ] Tests: legality, barrier legality + quota, both capture variants, survival, scoring
- **🚪 GATE:** two agents move legally on the grid; over-quota barrier rejected;
  coordinate overlap triggers capture; a full race runs to termination

---

## Stage 2 — FastMCP Infrastructure → [PRD-2](prd/PRD-2-mcp-infrastructure.md)

- [ ] FastMCP server instance, `mcp.run(transport="http", host="0.0.0.0", port=my_port)`
- [ ] Client engine calling the opponent's tools at `opponent_url`
- [ ] Tools: `handshake`, `negotiate_config`, `receive_move`, `get_state_digest`, `ping`
- [ ] Tool: `declare_barrier(position, step)` — truthful, exact, every placement
- [ ] Tool: `capture_claim(step)`
- [ ] Input validation on every tool — never trust an unverified move
- [ ] **Orchestrator** as single gateway to all five subsystems
- [ ] `GamePhaseMachine` with the transition table; illegal transition raises
- [ ] **Deadline Tracker**: timestamp + expiry on every request, controlled retry
- [ ] **Watchdog**: heartbeat monitor, state persistence, controlled shutdown
- [ ] Turn scheduler with strict alternation
- [ ] **Separation audit**: cop and thief in separate processes, separate config
      dirs, zero shared memory/modules/variables
- [ ] Tests: no placement path bypasses declaration; illegal transition; opponent
      killed mid-turn; watchdog freeze
- **🚪 GATE:** a geometric message from agent A over localhost is received and
  parsed correctly by agent B

---

## Stage 3 — Blind Strategy → [PRD-3](prd/PRD-3-blind-strategy.md)

- [ ] `PoliceBrain(BrainBase)` with `_pick_move` **and `_decide_move`** (barrier),
      selectable via `[strategy] police_class`
- [ ] Insertion point verified: after hint decode, before Commit pack
- [ ] Manhattan distance evaluation; **minimise** distance to the target
- [ ] Tie-break by containment value (escape-area reduction / edge proximity)
- [ ] Barrier value scorer: escape-area reduction, chain completion, self-penalty
- [ ] **Self-preservation constraint**: reject placements that disconnect us from
      the target region
- [ ] Barrier budget curve + 2–3 barrier endgame reserve
- [ ] Take a one-placement-away trapping or enclosure win when available
- [ ] Movement-forfeit cost comparison before every placement
- [ ] Legality guard: policy output re-validated against PRD-1 rules
- [ ] Determinism: seeded randomness, seed logged
- [ ] Decision on movement policy route recorded for the README (heuristic / own
      algorithm / RL) with justification
- [ ] Tests: never-illegal property test; self-wall-off regression board;
      quota never exceeded; determinism
- **🚪 GATE:** given a known target position, the agent computes and executes the
  shortest pursuit path with no manual intervention

---

## Stage 4 — Language & Scent → [PRD-4](prd/PRD-4-language-and-scent.md)

- [x] 5×5 radial scent emission, centre τ = 0.9 — emitted by the live match loop
      on **every** action, `STAY` and barrier turns included
- [x] Decay `τ(t+1) = max(0, (1−ρ)τ(t) + Δτ)`, ρ = 0.10, at end of each **full** turn
- [x] Sample **opponent's** field only; never our own
- [x] Fixture test against hand-computed decay values
- [x] **Pre-series lock**: exchange emission/decay model + numeric example, hash it
      — `Orchestrator.agree_scent_model` offers it through `negotiate` and refuses
      the series on any disagreement; `MatchRunner.agree` runs it after the config
      digest and no sub-game opens without one
- [x] Offer our scent-engine code to the opponent (permitted and recommended)
      — `SOURCE_OFFER` travels in the lock message, outside the digest
- [x] Belief map `b(s)` over the grid; zero belief on barriers, updated from the
      opponent's field at the full-turn boundary
- [x] Scent snapshot transmitted in **phase 3** and sealed into the **phase-1**
      SHA-256 commitment; a field edited after the commit fails verification
- [x] Final audit re-derives the opponent's trail from the agreed start and the
      revealed movement history; an impossible, malformed, non-finite, negative,
      out-of-range or over-limit field is an audit failure
- [x] Fail-closed: a peer that cannot bind its scent is refused rather than
      believed — unverified scent is never absorbed
- [ ] Bayes update combining scent evidence + hint, with reliability coefficient
- [ ] Adaptive reliability: lower on each detected contradiction
- [ ] Lie detector: expected-vs-measured scent contradiction (reproduce book example)
- [ ] Re-aim pursuit toward the true scent source after a detected lie
- [ ] Handle split probability mass (two foci) without oscillating
- [ ] Belief-weighted barrier scoring
- [ ] Natural-language hint parser (**no numeric-coordinate protocol** — forbidden)
- [ ] Hint generator with `hint_max_words` = 15 cap and `map_area` landmarks
- [ ] **`Intent` flag** (`truth`/`lie`) chosen before sending
- [ ] **Self-consistency guard**: reject any hint contradicting our own emitted field
- [ ] LLM providers: `template` (default, 0 tokens), `ollama`, `claude_api`, `claude_cli`
- [ ] `every_n_steps` throttle; `step_deadline_seconds` = 30 cap with template fallback
- [ ] Token metering
- **🚪 GATE:** free-language report → inference; scent map updates and decays each
  step; LLM produces a hint (truth or lie) within the word cap

---

## Stage 5 — Cloud Exposure → [PRD-5](prd/PRD-5-tunneling.md)

- [ ] ngrok / Localtonet tunnel exposing the FastMCP server publicly
- [ ] Public URL exchanged in handshake, recorded in the declaration file
- [ ] `opponent_url` switched from localhost to the public tunnel URL
- [x] Re-handshake path for a changed tunnel URL between sub-games
- [ ] Latency measured; `response_timeout_sec` justified against real round-trips
