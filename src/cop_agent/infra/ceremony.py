# mypy: ignore-errors
# ruff: noqa
from ._ceremony_acknowledgement_1 import _AcknowledgementMixin1, _install as _install_ceremony_acknowledgement_1
from ._ceremony_auditresult_1 import _AuditResultMixin1, _install as _install_ceremony_auditresult_1
from ._ceremony_commitment_1 import _CommitmentMixin1, _install as _install_ceremony_commitment_1
from ._ceremony_finalreveal_1 import _FinalRevealMixin1, _install as _install_ceremony_finalreveal_1
from ._ceremony_matchceremony_1 import _MatchCeremonyMixin1, _install as _install_ceremony_matchceremony_1
from ._ceremony_reveal_1 import _RevealMixin1, _install as _install_ceremony_reveal_1
from ._ceremony_stepceremony_1 import _StepCeremonyMixin1, _install as _install_ceremony_stepceremony_1
from ._ceremony_stepceremony_2 import _StepCeremonyMixin2, _install as _install_ceremony_stepceremony_2
import re
import secrets
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from ..domain.board import BoardState
from ..domain.crypto import NONCE_BYTES, commit_of, step_record
DIGEST = re.compile(r"^[0-9a-f]{64}$")
NONCE = re.compile(rf"^[0-9a-f]{{{NONCE_BYTES * 2}}}$")
COMMIT_FIELDS = ("step", "sender", "commit", "timestamp", "game_uid", "sub_game")
class CeremonyError(ValueError):
    pass
@dataclass(frozen=True, slots=True)
class Commitment(_CommitmentMixin1):
    step: int
    sender: str
    commit: str
    timestamp: str
    game_uid: str = "series-123"
    sub_game: int = 2
ACK_FIELDS = ("step", "sender", "acknowledges", "timestamp")
@dataclass(frozen=True, slots=True)
class Acknowledgement(_AcknowledgementMixin1):
    step: int
    sender: str
    acknowledges: str
    timestamp: str
REVEAL_FIELDS = (
    "step",
    "sender",
    "move",
    "intent",
    "hint",
    "barrier_placed",
    "scent",
    "timestamp",
    "game_uid",
    "sub_game",
)
@dataclass(frozen=True, slots=True)
class Reveal(_RevealMixin1):
    step: int
    sender: str
    move: str
    intent: str
    hint: str
    timestamp: str
    game_uid: str = "series-123"
    sub_game: int = 2
    barrier_placed: list[int] | None = None
    scent: dict[str, float] | None = None
@dataclass
class StepCeremony(_StepCeremonyMixin1, _StepCeremonyMixin2):
    step: int
    role: str
    ours: Commitment | None = None
    theirs: Commitment | None = None
    ack_sent: Acknowledgement | None = None
    ack_received: Acknowledgement | None = None
    revealed_ours: Reveal | None = None
    revealed_theirs: Reveal | None = None
    our_nonce: str | None = None
@dataclass(frozen=True, slots=True)
class FinalReveal(_FinalRevealMixin1):
    sender: str
    nonces: dict[int, str]
    timestamp: str
@dataclass
class MatchCeremony(_MatchCeremonyMixin1):
    role: str
    steps: dict[int, StepCeremony] = field(default_factory=dict)
    over: bool = False
class Verdict(Enum):
    CLEAN = "clean"
    FORGED = "forged"
@dataclass(frozen=True, slots=True)
class AuditResult(_AuditResultMixin1):
    verdict: Verdict
    checked: int
    failures: tuple[str, ...] = ()
def verify_step(record: dict[str, Any], nonce: str, commit: str) -> bool:
    return secrets.compare_digest(commit_of(record, nonce), commit)
def audit_opponent(
    match: MatchCeremony,
    disclosed: FinalReveal,
    sealed_states: dict[int, BoardState],
) -> AuditResult:
    failures: list[str] = []
    checked = 0
    for step in sorted(match.steps):
        ceremony = match.steps[step]
        if ceremony.theirs is None:
            continue
        checked += 1
        opened, nonce = ceremony.revealed_theirs, disclosed.nonces.get(step)
        if opened is None:
            failures.append(f"step {step}: committed but never revealed")
            continue
        if nonce is None:
            failures.append(f"step {step}: committed but no nonce disclosed")
            continue
        if step not in sealed_states:
            failures.append(f"step {step}: no board state to re-derive against")
            continue
        record = step_record(
            sealed_states[step],
            opened.sender,
            opened.move,
            opened.intent,
            opened.hint,
            barrier_placed=(
                (opened.barrier_placed[0], opened.barrier_placed[1])
                if opened.barrier_placed
                else None
            ),
            scent=opened.scent,
            game_uid=opened.game_uid,
            sub_game=opened.sub_game,
        )
        if not verify_step(record, nonce, ceremony.theirs.commit):
            failures.append(
                f"step {step}: committed {ceremony.theirs.commit[:16]}… but the revealed "
                f"move {opened.move!r} under the disclosed nonce produces "
                f"{commit_of(record, nonce)[:16]}…"
            )
    return AuditResult(
        verdict=Verdict.FORGED if failures else Verdict.CLEAN,
        checked=checked,
        failures=tuple(failures),
    )
_install_ceremony_acknowledgement_1(globals())
_install_ceremony_auditresult_1(globals())
_install_ceremony_commitment_1(globals())
_install_ceremony_finalreveal_1(globals())
_install_ceremony_matchceremony_1(globals())
_install_ceremony_reveal_1(globals())
_install_ceremony_stepceremony_1(globals())
_install_ceremony_stepceremony_2(globals())
