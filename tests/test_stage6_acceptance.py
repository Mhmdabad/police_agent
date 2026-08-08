import json
from dataclasses import dataclass
from cop_agent.domain.board import BoardState
from cop_agent.domain.crypto import commit_of, nonce, step_record
from cop_agent.infra.ceremony import (
    Acknowledgement,
    Commitment,
    FinalReveal,
    MatchCeremony,
    Reveal,
    Verdict,
    audit_opponent,
)
from cop_agent.infra.match_log import MatchLog
WHEN = "2026-08-04T09:00:00+00:00"
STEPS = 6
GRID = 8
def board(step: int) -> BoardState:
    return BoardState(
        grid_size=GRID, cop=(1, step % GRID), thief=(6, 5), barriers=frozenset(), step=step
    )
class Wire:
    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []
    def carry(self, kind: str, payload: dict[str, object]) -> dict[str, object]:
        self.sent.append((kind, json.dumps(payload, sort_keys=True)))
        landed: dict[str, object] = json.loads(json.dumps(payload))
        return landed  # a real round trip, not the same object
    @property
    def transcript(self) -> str:
        return "\n".join(body for _, body in self.sent)
class Peer:
    def __init__(self, role: str, wire: Wire) -> None:
        self.role = role
        self.wire = wire
        self.match = MatchCeremony(role=role)
        self.log = MatchLog(game_id="uoh26-s82kma9e", sub_game=1, role=role)
        self.records: dict[int, dict[str, object]] = {}
    def commit(self, step: int, move: str, hint: str) -> dict[str, object]:
        record = step_record(board(step), self.role, move, "truth", hint)
        secret = nonce()
        self.records[step] = record
        commitment = Commitment(
            step=step, sender=self.role, commit=commit_of(record, secret), timestamp=WHEN
        )
        self.match.at(step).commit(commitment, secret)
        self.log.commit(step, commitment.commit)
        return self.wire.carry("commit", commitment.to_dict())
    def reveal(self, step: int, move: str, hint: str) -> dict[str, object]:
        opened = Reveal(
            step=step, sender=self.role, move=move, intent="truth", hint=hint, timestamp=WHEN
        )
        self.match.at(step).reveal(opened)
        self.log.reveal(step, self.records[step])  # the sealed record, not the message
        return self.wire.carry("reveal", opened.to_dict())
    def final_reveal(self) -> dict[str, object]:
        self.match.finish()
        disclosed = self.match.final_reveal(WHEN)
        for step, secret in disclosed.nonces.items():
            self.log.disclose(step, secret)
        return self.wire.carry("final_reveal", disclosed.to_dict())
@dataclass
class Played:
    cop: Peer
    thief: Peer
    wire: Wire
    cop_disclosure: FinalReveal
    thief_disclosure: FinalReveal
    @property
    def states(self) -> dict[int, BoardState]:
        return {step: board(step) for step in range(1, STEPS + 1)}
def play(corrupt_at: int | None = None) -> Played:
    wire = Wire()
    cop, thief = Peer("police", wire), Peer("thief", wire)
    for step in range(1, STEPS + 1):
        cop.match.at(step).receive(Commitment.from_dict(thief.commit(step, "S", f"t{step}")))
        thief.match.at(step).receive(Commitment.from_dict(cop.commit(step, "N", f"c{step}")))
        theirs = wire.carry("ack", thief.match.at(step).acknowledge(WHEN).to_dict())
        ours = wire.carry("ack", cop.match.at(step).acknowledge(WHEN).to_dict())
        cop.match.at(step).receive_ack(Acknowledgement.from_dict(theirs))
        thief.match.at(step).receive_ack(Acknowledgement.from_dict(ours))
        thief_move = "W" if step == corrupt_at else "S"
        cop.match.at(step).receive_reveal(
            Reveal.from_dict(thief.reveal(step, thief_move, f"t{step}"))
        )
        thief.match.at(step).receive_reveal(Reveal.from_dict(cop.reveal(step, "N", f"c{step}")))
    from_thief = FinalReveal.from_dict(thief.final_reveal())
    from_cop = FinalReveal.from_dict(cop.final_reveal())
    cop.match.receive_final_reveal(from_thief)
    thief.match.receive_final_reveal(from_cop)
    return Played(cop, thief, wire, cop_disclosure=from_cop, thief_disclosure=from_thief)
