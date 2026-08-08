import json
from pathlib import Path
import pytest
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, step_record
from cop_agent.infra.ceremony import (
    ACK_FIELDS,
    COMMIT_FIELDS,
    REVEAL_FIELDS,
    Acknowledgement,
    CeremonyError,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
    StepCeremony,
    Verdict,
    audit_opponent,
    verify_step,
)
SRC = Path(__file__).parents[1] / "src" / "cop_agent"
DIGEST = "a" * 64
WHEN = "2026-08-04T09:00:00+00:00"
OUR_NONCE = "0" * 32
THEIR_NONCE = "1" * 32
BOARD = BoardState(grid_size=8, cop=(1, 2), thief=(6, 5), barriers=frozenset({(3, 3)}), step=4)
def commitment(**overrides: object) -> Commitment:
    fields: dict[str, object] = {
        "step": 4,
        "sender": "police",
        "commit": DIGEST,
        "timestamp": WHEN,
    }
    return Commitment(**{**fields, **overrides})  # type: ignore[arg-type]
THEIR_DIGEST = "b" * 64
def their_commitment(**overrides: object) -> Commitment:
    fields: dict[str, object] = {
        "step": 4,
        "sender": "thief",
        "commit": THEIR_DIGEST,
        "timestamp": WHEN,
    }
    return Commitment(**{**fields, **overrides})  # type: ignore[arg-type]
def opened() -> StepCeremony:
    ceremony = StepCeremony(step=4, role="police")
    ceremony.commit(commitment(), OUR_NONCE)
    ceremony.receive(their_commitment())
    return ceremony
def both_locked() -> StepCeremony:
    ceremony = opened()
    ceremony.acknowledge(WHEN)
    ceremony.receive_ack(
        Acknowledgement(step=4, sender="thief", acknowledges=DIGEST, timestamp=WHEN)
    )
    return ceremony
def reveal(**overrides: object) -> Reveal:
    fields: dict[str, object] = {
        "step": 4,
        "sender": "police",
        "move": "N",
        "intent": "lie",
        "hint": "heading uptown",
        "timestamp": WHEN,
    }
    return Reveal(**{**fields, **overrides})  # type: ignore[arg-type]
def played(steps: int = 3, role: str = "police") -> MatchCeremony:
    match = MatchCeremony(role=role)
    for step in range(1, steps + 1):
        match.at(step).commit(commitment(step=step), OUR_NONCE)
    return match
def sealed_state(step: int) -> BoardState:
    return BoardState(grid_size=8, cop=(1, 2), thief=(6, 5), barriers=frozenset(), step=step)
def honest_match(steps: int = 3) -> tuple[MatchCeremony, FinalReveal, dict[int, BoardState]]:
    match = MatchCeremony(role="police")
    states = {step: sealed_state(step) for step in range(1, steps + 1)}
    nonces: dict[int, str] = {}
    for step in range(1, steps + 1):
        record = step_record(states[step], "thief", "S", "truth", f"hint {step}")
        their_nonce = f"{step:032x}"
        nonces[step] = their_nonce
        ceremony = match.at(step)
        ceremony.commit(commitment(step=step), OUR_NONCE)
        ceremony.receive(their_commitment(step=step, commit=commit_of(record, their_nonce)))
        ceremony.acknowledge(WHEN)
        ceremony.receive_ack(
            Acknowledgement(step=step, sender="thief", acknowledges=DIGEST, timestamp=WHEN)
        )
        ceremony.receive_reveal(
            reveal(step=step, sender="thief", move="S", intent="truth", hint=f"hint {step}")
        )
    return match, FinalReveal(sender="thief", nonces=nonces, timestamp=WHEN), states
