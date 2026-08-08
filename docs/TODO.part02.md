- [ ] Retry policy applied to transport failures only — never to re-send an action
- [ ] Transport event logging (connect / timeout / retry / reconnect)
- [ ] Tunnel-drop test → controlled technical result, no hang
- **🚪 GATE:** an agent on a **remote machine** connects via ngrok and plays a full
  round against the local agent

---

## Stage 6 — Cryptography → [PRD-6](prd/PRD-6-crypto-commit-reveal.md)

- [ ] Nonce generator: `secrets.token_hex(16)` (**never** `random`)
- [ ] Canonical JSON serialisation (`sort_keys=True`, `separators=(",",":")`)
- [ ] `H_commit = SHA256(State ‖ Move ‖ Intent ‖ Nonce)` over the full step record
      (including barrier placement)
- [ ] Phase 1 Commit — hash only crosses the wire
- [ ] Phase 2 Acknowledge — opponent confirms lock
- [ ] Phase 3 Reveal — action + hint, **nonce stays hidden**
- [ ] Phase 4 Final Reveal / Audit — all nonces at end of match
- [ ] Verification with `secrets.compare_digest`; mismatch ⇒ `TECHNICAL_LOSS`
- [ ] Append-only log `log_<game_id>_g<NN>.json` with commit/reveal/nonce per step
- [ ] **Capture Claim guard**: no path emits a claim unsupported by `BoardState`
- [ ] Audit re-verifies every declared barrier against the committed one
- [ ] `Step-0`: OS, CPU cores/freq, RAM, GPU/VRAM, LLM model name
- [ ] `Step-0`: code version, team name, sub-game number, **GitHub commit hash**
- [ ] Step-0 declaration signed with the pre-supplied key
- [ ] Token consumption metered and cryptographically locked
- [ ] Cross-implementation fixture test: both peers hash byte-identical payloads
- [ ] Tests: corrupted reveal detected; nonce never leaked early; audit passes clean
- **🚪 GATE:** a move is committed then revealed with a valid nonce; Step-0 verifies
  hardware and commit hash on both sides

---

## Stage 7 — Reporting & Visualization → [PRD-7](prd/PRD-7-reporting-and-gui.md)

### GUI
- [x] Live GUI (Tkinter/PyQt) showing **local truth only** — never the thief's real cell
- [x] Belief heatmap bound to the real belief object (deeper red = higher probability),
      with `T?` at `argmax b(s)`, `C` at our position, dark cells for barriers
- [x] Turn banner: green `YOUR TURN` / grey `LOCKED`, with input lock after Commit

### Replay
- [x] Replay App loading `log_<game_id>_g<NN>.json`, step forward/backward
- [x] Per-step SHA-256 re-computation vs stored commitment
- [x] Green `Verified OK` / red `TAMPERED`; abort and void on first failure
- [x] Hand-tampered log test triggers `TAMPERED`

### Gmail + Gatekeeper
- [x] Google Cloud project + Gmail API enabled
- [x] OAuth Consent Screen configured, team members added as Test Users
- [x] Scope restricted to `https://www.googleapis.com/auth/gmail.send` **only**
- [x] OAuth Client ID (Desktop Application) → `credentials.json` **(gitignored)**
- [x] First authorization flow → `token.json` **(gitignored)**
- [x] **Quota Manager** — daily safety threshold
- [x] **Token Bucket** — 30 rpm, 2 concurrent, 5 s backoff, 3 retries, queue 100
- [x] **DOS Detector** — anomaly lock (backpressure / circuit breaker)
- [x] 429 handling: honour, back off, wait for next window — never blind retry
- [x] Report sent as **structured JSON attachment**, never free plaintext
- [x] Destination hard-coded: `rmisegal+uoh26finalgame@gmail.com`
- [x] Send-storm simulation blocked before reaching the API

### JSON artefacts
- [x] `declaration_<game_id>.json` — teams, members, **4 repo URLs**, MCP addresses,
      hardware, LLM model, token ceiling, start/end times
- [x] `config_<game_id>_g<NN>.json` — locked agreed parameters
- [x] `log_<game_id>_g<NN>.json` — full step record including barrier declarations
- [x] `result_<game_id>.json` — per-sub-game and aggregate scores, commit hashes,
      total tokens
- [x] Shared `game_uid`, names derived from `game_id`
- **🚪 GATE:** match summary sent via Gmail; GUI displays state; Replay App
  reconstructs a recorded round with `Verified OK`

---

## League play

- [x] Pre-match negotiation protocol: board, starts, barrier quota, `map_area`,
      timeouts, token ceiling
- [x] Exchange and verify `config_sha256`; **refuse to play on mismatch**
- [ ] **Game-count declaration** at the start of every match (a false declaration
      disqualifies the team)
- [ ] Warm-up matches against varied strategies (not counted — allowed and encouraged)
- [ ] **Counted match #1** vs team ___ — result agreed, both reports sent
- [ ] **Counted match #2** vs team ___ — result agreed, both reports sent
- [ ] (Optional, up to 10 total) further counted matches vs **different** teams
- [ ] One counted match per opponent — no repeats for points
- [ ] Mutual log audit completed after every match, before agreeing the result

---

## Submission

- [ ] `README.md` item 1 — Dec-POMDP model: state space, observations, uncertainty
- [ ] `README.md` item 2 — FastMCP orchestration dilemmas: turn management,
      network-failure handling, Gatekeeper and Orchestrator roles
- [ ] `README.md` item 3 — strategies implemented and why
- [ ] `README.md` item 4 — learning curves (**only if** RL was used)
- [ ] `README.md` item 5 — **screenshots: belief heatmap + Replay `Verified OK`**
- [ ] `README.md` item 6 — **cross-link to the thief repo**
- [ ] Any contradiction found in the rulebook documented: where, what we chose, why
- [ ] `config/` files for every match committed
- [ ] `docs/PLAN.md`, `docs/TODO.md`, `docs/prd/*` present (this set)
- [ ] Secrets audit: nothing sensitive anywhere in Git history
- [ ] Annotated tag pushed:
      `git tag -a v1.0-submission -m "Final submission: Police-Thief P2P, group N"`
- [ ] Moodle: Word template filled **without moving any field**, saved as PDF
- [ ] Moodle: **both** repo links (cop + thief) included
- [ ] Moodle: each group member submits separately
- [ ] Self-assessment score rates **code quality only**, not the league result

---

## Final pre-submission checklist (Rulebook §11.5)

- [ ] Base logic works: full race, no crash, scoring enforced
- [ ] FastMCP over a **public URL**, not just localhost
- [ ] Commit-Reveal active and the audit completes with no forgery detected
- [ ] Scent map and belief map computed **and actually influencing decisions**
- [ ] Live GUI and Replay App with a valid `Verified OK` stamp
- [ ] Gmail JSON reports sent **by both sides**
- [ ] GitHub repo with Git tag and academic README
- [ ] **At least 2 matches against different teams**
