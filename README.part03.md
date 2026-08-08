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
| 5 | **When the hint may be sent.** Ch. 5.3.2 puts an **Acknowledge** phase between Commit and Reveal, and states its purpose: the acknowledgement *"ensures the reveal happens only once both sides have already fixed their moves"*. The reference bundles commitment, hint and scent into a single `TurnMessage`, one round trip per turn. | The **PDF's four phases**, in `infra/ceremony.py`. The bundled `TurnMessage` shape is kept for an opponent who speaks only the reference dialect, so the difference costs a negotiation rather than a code change. | Under the bundled form, whichever peer sends second has read the first one's hint **before** choosing what to commit to — which is exactly the advantage the Acknowledge phase exists to remove. The two are not variants of one protocol: one of them contains the security property the chapter is about, and the other does not. |
| 6 | **Where the scent field travels, and whether anything binds it.** The rulebook puts the field in the environment and calls it unfalsifiable (ch. 4.4), but never says how a peer transmits one; the reference implementation ships it as `TurnMessage.smell_grid` **alongside the phase-1 commitment**, unbound and unchecked. | The field is disclosed in **phase 3**, sealed into the **phase-1 SHA-256 commitment**, and re-derived at the final audit from the agreed start and the revealed movement history. `domain/scent_audit.py` does the reconstruction; a peer that cannot bind its field is refused, explicitly and before the series, through the `binding` term in the pre-series scent lock. | Two separate problems, and the reference form has both. A fresh emission peaks on the emitter's own cell, so a field sent with the commitment discloses the exact position that commitment exists to conceal. And an unbound field can be chosen *after* reading the opponent's reveal — which makes "the scent cannot lie" false, since the field is now just another claim. Sealing it fixes the second; holding it to phase 3 fixes the first; and neither is enough on its own, because a sealed field can still be a field the physics could never have produced. Only re-deriving the trail turns *a hint may lie, a trail may not* into a property of the protocol rather than an aspiration about it. |

Entries 1, 2, 4, 5 and 6 are divergences between the rulebook and the reference code
published alongside it. In each case the **PDF is treated as authoritative** —
its own header states that the source PDF governs and that Appendix F is the
sole authority for quantitative parameters. The reference implementation is
treated as one more implementation we may have to negotiate against, not as a
standard.

Entry 6 is the one place this project **declines** the reference dialect outright rather
than keeping it as a negotiable alternative. There is no way to accept unbound scent that
does not give up both the secrecy of our position and the evidence the belief map is built
on, so the fallback is a series played with **no scent at all**, agreed in advance — never
a series played with scent nobody can check.

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
