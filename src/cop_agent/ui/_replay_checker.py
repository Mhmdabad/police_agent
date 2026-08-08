"""Helper step verification logic for replay UI."""

import secrets
from dataclasses import dataclass

from ..domain.crypto import CryptoError, commit_of
from .replay import RecordedStep


@dataclass(frozen=True, slots=True)
class StepCheck:
    """One step, re-derived."""

    step: int
    verified: bool
    reason: str = ""

    def __str__(self) -> str:
        return f"step {self.step}: {'ok' if self.verified else self.reason}"


def check_step(recorded: RecordedStep) -> StepCheck:
    """Recompute the digest from the sealed record and its nonce."""
    if not recorded.openable:
        missing = "no reveal" if recorded.reveal is None else "no nonce"
        return StepCheck(recorded.step, verified=False, reason=f"cannot be opened ({missing})")
    assert recorded.reveal is not None and recorded.nonce is not None
    try:
        recomputed = commit_of(recorded.reveal, recorded.nonce)
    except CryptoError as exc:
        return StepCheck(
            recorded.step,
            verified=False,
            reason=f"its recorded record cannot be hashed as the committer hashed it: {exc}",
        )
    if not secrets.compare_digest(recomputed, recorded.commit):
        return StepCheck(
            recorded.step,
            verified=False,
            reason=(
                f"commitment {recorded.commit[:16]}… but the recorded record under the "
                f"recorded nonce produces {recomputed[:16]}…"
            ),
        )
    sealed = recorded.reveal.get("state")
    if isinstance(sealed, dict) and sealed.get("step") != recorded.step:
        return StepCheck(
            recorded.step,
            verified=False,
            reason=(
                f"the record here is genuine but seals step {sealed.get('step')!r}; "
                "a real step filed under another number is a replay, not a record"
            ),
        )
    return StepCheck(recorded.step, verified=True)
