        {"state": state, "move": move, "intent": intent, "nonce": nonce},
        sort_keys=True, separators=(",", ":"))
    recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return secrets.compare_digest(recomputed, h_commit)
```

> The sketch shows the core; the record actually sealed in this project covers the
> full step — state, move (including barrier placement), intent, nonce, hint,
> verdict, step index, role and sub-game.

## 6. Acceptance criteria (milestone gate)

- [ ] A move is committed, then revealed, with a valid nonce; the opponent's
      verification passes.
- [ ] A barrier placement is committed, declared, and re-verified at audit.
- [ ] A deliberately corrupted reveal is detected and produces `TECHNICAL_LOSS`.
- [ ] Nonces are never transmitted before the final audit (protocol test).
- [ ] Both peers hash byte-identical payloads (cross-implementation fixture test).
- [ ] `Step-0` verifies hardware, code version and commit hash on both sides.
- [ ] No code path can emit a Capture Claim unsupported by `BoardState`
      (unit + property test).
- [ ] Full end-of-match audit completes with no tampering detected.
- [ ] Token totals are metered and locked.

## 7. Out of scope / deferred

Replay viewer UI and `Verified OK` / `TAMPERED` banners (PRD-7) · Gmail delivery
of the signed report (PRD-7).
