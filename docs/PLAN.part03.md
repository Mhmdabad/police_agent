    "pheromone_grid_size": 5
  },
  "network_and_league": {
    "response_timeout_sec": 30, "watchdog_timeout_sec": 60,
    "num_games": 6, "diversity_reward": 10,
    "min_games_to_pass": 2, "max_games_per_team": 10,
    "token_budget_per_series": 200000
  },
  "rate_limiter_gatekeeper": {
    "requests_per_minute": 30, "concurrent_requests": 2,
    "retry_backoff_sec": 5, "max_retries": 3, "queue_depth": 100
  }
}
```

A full league series against one opponent is **6 sub-games**, and Appendix F
table 18 row 1 marks that **fixed** — deviating disqualifies the team, so there
is no demo-sized default to fall back to. Each config file must be **named per
match** and committed to this repo so any match is reproducible.

---

## 7. Build order — seven layers, seven PRDs

Incremental delivery: each layer runs **end-to-end** before the next is laid on
top, so at any moment the space of possible faults is confined to the newest
layer. Skipping ahead to crypto or the cloud does not save time — it doubles it.

| Stage | PRD | Builds | Rulebook |
|---|---|---|---|
| 1 | [PRD-1](prd/PRD-1-base-logic.md) | Grid, movement rules, barriers, capture detection — one process | Ch. 3 |
| 2 | [PRD-2](prd/PRD-2-mcp-infrastructure.md) | FastMCP servers + geometric tools over localhost | Ch. 2 |
| 3 | [PRD-3](prd/PRD-3-blind-strategy.md) | Blind strategy module (full information, no fog) | Ch. 6 |
| 4 | [PRD-4](prd/PRD-4-language-and-scent.md) | Natural-language hints, scent emission/decay, belief map, LLM bluffing | Ch. 4, 6 |
| 5 | [PRD-5](prd/PRD-5-tunneling.md) | Public URLs via ngrok / Localtonet, remote play | Ch. 2 |
| 6 | [PRD-6](prd/PRD-6-crypto-commit-reveal.md) | Commit-Reveal, nonce generator, Step-0 declarations, audit | Ch. 5 |
| 7 | [PRD-7](prd/PRD-7-reporting-and-gui.md) | Gmail API over OAuth 2.0, Live GUI, Replay App | Ch. 9, 7, App. A |

Milestone gate for each stage: **behaviour observed end-to-end**, not "code
written". See [TODO.md](TODO.md) for the checkable form of each gate.

---

## 8. League participation

- Minimum to pass: **2 counted matches against different teams**. Maximum: **10**.
- **One counted match per opponent.** Warm-ups that are not counted are allowed
  and encouraged.
- At the start of every match each team **declares how many counted matches it
  has already played**; the diversity incentive is weighted from those mutual
  declarations. A false declaration discovered at grading **disqualifies the team**
  — and since both sides email their reports, the lecturer always knows the truth.
- At the end of every legal match both teams must **agree on the result** and each
  team **sends its own JSON report** to `rmisegal+uoh26finalgame@gmail.com`. If one
  side does not report, that side gets no points — even if it won on the board.
  Contradictory reports void the match and score 0 for both.
- **Computational fairness:** the league normalises for hardware. A lean algorithm
  on a modest laptop scores better than a wasteful one on a server farm. This is a
  direct argument for the zero-token `template` bluff provider (or local Ollama)
  and a tight, deterministic move policy.

---

## 9. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Barrier walls the cop off from the thief | Placement scorer rejects any barrier that disconnects us from `argmax b(s)`; reachability check before every placement |
| Barrier budget exhausted too early | Budget curve tied to belief concentration; hold a 2–3 barrier endgame reserve |
| Tunnel drops mid-turn → deadlock | Deadline Tracker on every request + Watchdog; controlled shutdown with state persistence rather than silent freeze |
| Config drift between peers | Exchange `config_sha256` before move 1; refuse to play on any mismatch |
| Scent formula interpreted differently | Lock the model + a numeric example by hash pre-series; offer the opponent our scent-engine code |
| LLM latency/blocking stalls a turn | `step_deadline_seconds = 30` hard cap; fall back to `template` provider; `every_n_steps` throttling |
| Gmail 429 / account suspension | Gatekeeper: Quota Manager → Token Bucket → DOS Detector; honour 429 with back-off, never retry blindly |
| Secret leak (`credentials.json`, `token.json`) | `.gitignore` before first commit; a leaked secret is permanently compromised — rotate in the console |
| Premature or wrong capture claim | Claim only from verified `BoardState` overlap or a trapping/enclosure condition; a false claim = immediate disqualification |
| Over-fitting to one opponent | Warm-up matches against varied strategies; never tune to a single adversary |

---

## 10. Definition of done

- [ ] Base logic runs a full race without crashing; scoring enforced correctly.
- [ ] FastMCP P2P over a **public URL**, not just localhost.
- [ ] Commit-Reveal active; full audit completes with no tampering detected.
- [ ] Scent map and belief map computed **and actually influencing decisions**.
- [ ] Live GUI + Replay App showing `Verified OK`.
- [ ] Gmail JSON reports sent **by both sides** after each match.
- [ ] GitHub repo accessible to the lecturer, annotated tag `v1.0-submission` pushed.
- [ ] README academic report complete (6 mandatory items) with screenshots.
- [ ] Cross-link to the thief repo present in the README.
- [ ] `.gitignore` verified: no secrets in history.
- [ ] ≥ 2 counted matches against different teams.

---

## 11. Reference material

- Reference implementation (study only, **not** a submission skeleton):
  <https://github.com/rmisegal/Game-P2P-Cop-Chase>
- Lecturer (general / repo sharing): `rmisegal@gmail.com`
- Agent report target (mandatory, hard-coded): `rmisegal+uoh26finalgame@gmail.com`
- Where the book and the reference repo disagree, **the book and Appendix F win**.
