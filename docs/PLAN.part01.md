# PLAN — COP Agent (שוטר)

**Project:** Distributed Cops-and-Robbers over a Peer-to-Peer Network
**Course:** Orchestration of AI Agents — CS Dept., University of Haifa, 2026
**Rulebook:** `police_thief_p2p.pdf`, book version 3.0.0 (Dr. Yoram Reuven Segal)
**This repo:** COP agent. Companion repo: **THIEF agent** — [theif_agent](https://github.com/Mhmdabad/theif_agent)

---

## 1. What we are building

Two **symmetric, autonomous agents** — a COP and a THIEF — race each other on a
discrete grid **with no central server and no referee**. Neither agent sees the
true world state. Each builds a *belief* about its opponent's position from
(a) a decaying **scent map** the opponent cannot fake, and (b) a **verbal hint**
that may be a deliberate lie.

Formally this is a **Dec-POMDP** (Decentralized Partially Observable Markov
Decision Process). Practically it is a P2P network where each agent is
*simultaneously an MCP server and an MCP client* over **FastMCP**, and where
integrity is enforced by **Commit-Reveal over SHA-256** instead of by a judge.

This repository contains **only the COP**. The THIEF lives in a separate repo and
must run as a **completely separate process with a separate config directory**
(`config/police/` here, `config/thief/` there). Sharing memory, importing a module
that holds live state, or reading shared variables between the two sides
**disqualifies the solution** even if the game "works" technically
(Rulebook §2.4.2, Appendix E rules 1–2).

### The COP's asymmetric position

| | **COP (this repo)** | THIEF |
|---|---|---|
| Goal | **Land on the thief's cell and claim capture** | Survive `survival_threshold` valid steps |
| Special power | **Place barriers — architect of the arena** | None — pure evasion |
| Best score | **20 (capture)** | 10 (survival) |
| Consolation | 5 (thief survives) | 5 (captured) |
| Start (default) | **corner `[0,0]`** | centre `[3,3]` |

The scoring is deliberately asymmetric: capture is the cop's highest reward and
embodies its main goal, while patient survival is the thief's. A technical loss
zeroes **both** sides, so neither can win "on the clock".

### The barrier rule — our defining capability

On a turn where the cop **forfeits movement**, it may place a physical barrier on
**any cell within one step**: its own cell or one of the four orthogonally
adjacent cells. That cell becomes impassable **for both players until the end of
the match**. Barriers are irreversible — a blocked cell stays blocked.

Two consequences that are outright win conditions:

- **Trapping placement:** if the cop places a barrier on the cell the thief
  currently occupies — **the thief is captured**.
- **Enclosure:** a thief left with no legal move at all (all neighbours blocked by
  barriers and/or the board edge) is **likewise considered captured**.

The quota is `max_barriers` (default **14**, minimum). Every placement is therefore
a **resource-management decision**: squeeze the thief toward a corner without
accidentally walling off our own access routes. A greedy barrier can imprison the
cop behind a wall of its own making, or open the thief a fresh escape corridor.
When to block, where, and how many to hold back for the endgame is a strategic
problem in its own right — and it is where this agent's grade is won.

**Declaration duty:** every barrier placement must be **announced truthfully with
its exact location**. No hidden barriers, and the cop may not lie about the
location (Appendix E rules 15–16).

---

## 2. Architectural shape

```
                    ┌──────────────────────────────┐
                    │      Orchestrator            │  single gateway;
                    │      (Gateway)               │  coordinates, never decides
                    └───┬───┬───┬────┬─────┬───────┘
                        │   │   │    │     │
        ┌───────────────┘   │   │    │     └──────────────┐
        ▼                   ▼   ▼    ▼                    ▼
  MCP Connector     Decision Module  Log Manager   Deadline Tracker   Watchdog
  (FastMCP          (Strategy:       (Commit-      (per-request       (heartbeat,
   server+client)    belief, move,    Reveal log,   expiry, retry)     controlled
                     barrier, hint)   audit)                           shutdown)
```

Hard rules that shape this design (Appendix E):

- The **Orchestrator is the single entry point** to every subsystem; peripheral
  modules never talk to each other directly (rule 3).
- Game phases run through a **strict state machine**; illegal transitions are
  rejected immediately (rules 4–5).
- **Deadline Tracker** on every MCP request and a **Watchdog** over the main loop
  (rules 6–7). A missed deadline is a *failure*, not an invitation to wait longer.
- The **Live GUI shows local truth only** — never a bird's-eye view of the real
  board (rules 8–9).
- The server is exposed to the public internet through a **tunnel** (rule 10);
  `localhost` is allowed only during early coding.

### Game-turn state machine

```
WAITING_FOR_OPPONENT → COMPUTING_MOVE → COMMITTING → AWAITING_REVEAL → VERIFYING
        ▲                                                                   │
        └───────────────────────────────────────────────────────────────────┘
              (any communication phase may exit to TECHNICAL_LOSS)
```

`TECHNICAL_LOSS` is terminal and scores **0 for both sides** — which is why
protocol hygiene matters more than winning a single board.

### Strategy module boundary

The strategy module plugs into the `PeerRuntime` at exactly one point:
**after decoding the incoming hint, before packing the outgoing Commit.**

```
incoming hint + scent → hint decode → belief update (Bayes)
                                            ↓
Commit pack (out)  ←  LLM bluff text  ←  move / barrier choice (algorithmic)
```

**The LLM never chooses the move.** LLMs hallucinate in Cartesian space — they
confuse directions, distances and coordinates, and will confidently return an
illegal or suicidal move (Rulebook §6.5). The LLM writes text and profiles the
opponent's language; the algorithm owns every spatial decision. (An LLM-driven
move policy is permitted *only* by explicit, documented mutual agreement of both
teams — and even then the local algorithm must still reject illegal moves.)

---

## 3. Movement + barrier policy — our choice

The book offers three **equal-standing** options for the move policy:

1. **Pure heuristics** — Bayesian belief map + Manhattan distance. Deterministic,
   transparent, easy to debug, frequently competitive. *Reference default.*
2. **Your own heuristic algorithm** — belief + scent + **barrier exploitation** +
   lookahead (minimax / expectimax against the opponent's belief).
3. **Reinforcement learning (Q-Learning / Bellman)** — explicitly **optional**;
