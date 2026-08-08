### 5.4 OAuth 2.0 setup (Appendix A)
- FR-7.24 Five ordered steps: (1) create a Google Cloud project and enable the
  Gmail API; (2) configure the **OAuth Consent Screen** and add team members as
  Test Users; (3) restrict the scope to the absolute minimum; (4) create an OAuth
  Client ID of type **Desktop Application** and download `credentials.json`;
  (5) run the first authorization flow, which generates `token.json`. Skipping a
  step — especially the consent screen — makes the flow fail later and more
  confusingly.
- FR-7.25 **Scope: `https://www.googleapis.com/auth/gmail.send` only.** Never grant
  read or modify access. Least privilege turns a stolen token from a powerful
  weapon into a nearly harmless tool.
- FR-7.26 `token.json` holds a short-lived **Access Token** plus a long-lived
  **Refresh Token**; thanks to the latter the agent reports autonomously for months
  with no further manual intervention.
- FR-7.27 **`credentials.json` and `token.json` are secrets.** Both **must** be
  listed in `.gitignore` **before the first commit** — this applies even to a
  private repo shared only with the lecturer. A secret pushed even once is
  permanently compromised: deleting it from current code is not enough, the
  credentials must be **rotated** in the console.

---

## 6. The four mandatory JSON files

All four share a common `game_uid`, and each filename derives from `game_id`, so
files from different matches can never be mixed up.

| Variable | Filename | Role |
|---|---|---|
| Declaration file | `declaration_<game_id>.json` | Pre-game declaration: both teams and members, **cop and thief repo URLs**, MCP server addresses, hardware specs, LLM model, agreed token ceiling, start/end times. Fixes cryptographically everything that does not change during the match. |
| Config file | `config_<game_id>_g<NN>.json` | The agreed configuration: all quantitative sub-game parameters (Appendix F), cryptographically locked and identical on both sides. |
| Log file | `log_<game_id>_g<NN>.json` | Step-by-step record: Commit-Reveal commitments, moves, barrier declarations, hints, LLM discussion fields, nonces and hashes. Enables full verification in the Replay App. |
| Result file | `result_<game_id>.json` | Final results report: each team's score per sub-game and the aggregate, for league weighting. **This is the binding report emailed to the lecturer.** |

- FR-7.28 Mandatory fields include **both teams' GitHub links (four links total)**,
  the **commit hash of each sub-game**, and **total tokens consumed**.

---

## 7. Submission artefacts

- FR-7.29 **Two separate GitHub repos** — cop and thief — each accessible to the
  lecturer (public, or private and explicitly shared with `rmisegal@gmail.com`).
- FR-7.30 **Mandatory cross-link:** each repo's `README.md` links to the team's
  other repo. This repo (COP) links to the THIEF repo, and vice versa. The Moodle
  submission carries **both** links; the end-of-match JSON carries **four**.
- FR-7.31 Each repo contains at minimum: `README.md` (the academic report),
  `config/`, the **PRD** files, the **PLAN** file, and the **TODO** files. These
  tell the story of development and let the grader reconstruct the working method
  — not just the final result.
- FR-7.32 Final version fixed with an **annotated Git tag**:

  ```bash
  git tag -a v1.0-submission -m "Final submission: Police-Thief P2P, group N"
  git push origin v1.0-submission
  ```
  Development runs on feature branches, merged to main only once stable.
- FR-7.33 `README.md` academic report — six mandatory components:
  1. **The chosen Dec-POMDP model** — scientific description of the formalism:
     state space, observations, uncertainty.
  2. **FastMCP orchestration dilemmas** — turn management, network-failure
     handling, the roles of Gatekeeper and Orchestrator.
  3. **Strategies implemented** — heuristics (Manhattan, Bayesian belief),
     LLM-based strategy, or optionally Q-Learning.
  4. **Learning curves** — mandatory **if** RL was used, as empirical evidence of
     policy convergence.
  5. **Screenshots — absolute requirement** — the Live GUI belief map and the
     Replay App showing `Verified OK`.
  6. **Link to the companion repo** (cop ↔ thief).
- FR-7.34 Moodle: each group member submits separately; the group gets a unique
  **8-character identifier with no spaces**; the Word template is filled in and
  saved as PDF **without moving or changing any field**.
- FR-7.35 The self-assessment score must rate **code quality only — never the
  league result**. Basing it on the match outcome distorts the code-quality
  criterion.

## 8. Acceptance criteria (milestone gate)

- [ ] Match summary sent through Gmail as a structured JSON attachment.
- [ ] GUI displays live state under local truth only; banner locks input after commit.
- [ ] Replay App reconstructs a recorded round and stamps `Verified OK`.
- [ ] A hand-tampered log triggers `TAMPERED` and voids the match.
- [ ] Gatekeeper blocks a simulated send storm before it reaches the API.
- [ ] A 429 is honoured with back-off, not an immediate retry.
- [ ] All four JSON files generated with consistent `game_uid` and derived names.
- [ ] `.gitignore` verified — no `credentials.json` / `token.json` anywhere in history.
- [ ] `v1.0-submission` tag pushed; README complete with screenshots and cross-link.
