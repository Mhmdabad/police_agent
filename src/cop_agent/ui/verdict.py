"""The stamp the Replay App puts on a log, and the walk that earns it.

FR-7.12: green ``Verified OK`` on clean match, red ``TAMPERED`` on alteration.
FR-7.13: abort walk on first failure.

Three outcomes:
* every step re-derived and matching → ``Verified OK``;
* a step that opens and **disagrees** → ``TAMPERED``, void;
* a step that **cannot be opened** → ``INCOMPLETE``.
"""

from dataclasses import dataclass
from enum import Enum

from .replay import Replay, check_step


class Stamp(Enum):
    """The verdict, and the colour the rulebook asks it to be shown in."""

    VERIFIED_OK = "green"
    """Every step re-derived from the log itself and matched."""

    TAMPERED = "red"
    """A step opened and did not produce its commitment. The match is void."""

    INCOMPLETE = "grey"
    """A step could not be opened. Nothing proven, and nothing cleared."""

    @property
    def text(self) -> str:
        """The words on the stamp, spelled as the rulebook spells them."""
        return {
            Stamp.VERIFIED_OK: "Verified OK",
            Stamp.TAMPERED: "TAMPERED",
            Stamp.INCOMPLETE: "INCOMPLETE",
        }[self]


@dataclass(frozen=True, slots=True)
class Attestation:
    """What the walk found, and which step the verdict is about.

    Carries ``verified`` and ``at_step`` alongside the stamp because a red
    banner on its own is an accusation nobody can check. "Step 7 committed to a
    digest its own recorded record and nonce do not produce" is one the other
    team can run themselves and get the same answer — which is the only kind of
    finding that settles anything.
    """

    stamp: Stamp
    verified: int
    total: int
    at_step: int | None = None
    """The step the verdict names: the forged one, or the first unopenable one."""

    unopened: tuple[int, ...] = ()
    """Steps passed over because they could not be re-derived."""

    reason: str = ""

    @property
    def clean(self) -> bool:
        return self.stamp is Stamp.VERIFIED_OK

    @property
    def void(self) -> bool:
        """Whether this result voids the match. No appeal, no retroactive fix."""
        return self.stamp is Stamp.TAMPERED

    def __str__(self) -> str:
        if self.clean:
            return f"{self.stamp.text} — {self.verified} steps re-derived"
        return (
            f"{self.stamp.text} at step {self.at_step} — "
            f"{self.verified} of {self.total} steps re-derived, then {self.reason}"
        )


def walk(replay: Replay) -> Attestation:
    """Re-derive the log in order, aborting the moment a step fails to hold.

    Aborting on a mismatch is the rulebook's instruction and it is also the
    honest thing to report. Once one step is forged the match is void, so the
    steps after it are not evidence of anything — checking them would only
    invite an argument about how many were wrong, when the answer is *enough*.

    A step that cannot be **opened** does not abort the walk, and that
    asymmetry is deliberate. Stopping there would let a cheat shield a forgery
    by deleting the nonce of some earlier step, so the walk passes over the gap
    and keeps looking. It still refuses to clear the log: gaps that survive to
    the end make the verdict ``INCOMPLETE``, never ``Verified OK``. Between the
    two, tampering wins — a proven forgery is a harder fact than a gap.

    Steps are walked in the log's own order rather than from the cursor, so
    the verdict does not depend on where the reader happens to be looking.
    """
    verified = 0
    total = len(replay.steps)
    unopened: list[int] = []
    gap = ""
    for recorded in replay.steps:
        if not recorded.openable:
            unopened.append(recorded.step)
            gap = gap or check_step(recorded).reason
            continue
        checked = check_step(recorded)
        if not checked.verified:
            return Attestation(
                Stamp.TAMPERED,
                verified,
                total,
                at_step=recorded.step,
                unopened=tuple(unopened),
                reason=checked.reason,
            )
        verified += 1
    if unopened:
        return Attestation(
            Stamp.INCOMPLETE,
            verified,
            total,
            at_step=unopened[0],
            unopened=tuple(unopened),
            reason=gap,
        )
    return Attestation(Stamp.VERIFIED_OK, verified, total)
