### 3.7 Decision flow (final shape of the strategy module)

```
incoming hint + thief scent
        ↓
   hint decode (parse text)
        ↓
   belief update (Bayes, reliability-weighted)
        ↓
   move OR barrier choice (algorithmic: pursuit + containment)
        ↓
   LLM / template bluff text (+ Intent flag)
        ↓
   Commit pack (out)
```

## 4. Acceptance criteria (milestone gate)

- [ ] A free-language report is translated into an inference (belief update).
- [ ] The scent map updates and decays on every step, matching the formula to
      within floating-point tolerance against a hand-computed fixture.
- [ ] The LLM (or template) produces a hint, correctly flagged `truth` or `lie`,
      within `hint_max_words`.
- [ ] The book's worked lie-detection example is reproduced by our detector and
      demonstrably re-aims the pursuit vector.
- [ ] Belief `argmax` demonstrably steers pursuit, and belief mass weights barrier
      scoring (log shows both).
- [ ] Split probability mass is handled without oscillation (regression test).
- [ ] A full series runs end-to-end in `template` mode at **zero tokens**.
- [ ] Our own hint generator never emits a hint that contradicts our own emitted
      scent field (guard test).

## 5. Out of scope / deferred

Public exposure (PRD-5) · commitment/reveal of move + hint + Intent (PRD-6) ·
heatmap rendering (PRD-7) · token reporting in the final JSON (PRD-7).
