"""The pre-series scent lock.

Exchanges emission and decay models, hashes agreement, and verifies terms match.
"""

from dataclasses import dataclass

from ..shared.config import canonical_bytes, config_sha256, digests_agree
from .fixture import BINDING, ScentFixture, build
from .scent import DEFAULT_FALLOFF, Falloff

SOURCE_OFFER = (
    "Our scent engine is offered in full: domain/scent.py (emission), "
    "domain/trail.py (merge and decay), domain/fixture.py (this example), "
    "domain/scent_audit.py (the reconstruction we will audit you with). "
    "The rulebook permits and recommends sharing it, and the physics are "
    "public and symmetric, so it costs nothing strategically and removes the "
    "last room for an interpretation difference. The auditor is included "
    "deliberately: a check the other side cannot run against itself first is "
    "a trap rather than an agreement."
)
"""Accompanies the proposal. The rulebook explicitly recommends this.

Offering the code is strictly stronger than agreeing a formula: a formula
still has to be read, and reading is where the two divergences already found
in this project came from.
"""


@dataclass(frozen=True, slots=True)
class ScentAgreement:
    """A lock the opponent matched exactly, and what the runtime may do about it.

    The output of the negotiation rather than an input to it, which is the whole
    of P1-15: ``SubGame.require_bound_scent`` used to be a ``True`` written in
    the source with no caller and no configuration behind it, so the fail-closed
    posture it documented was an edit rather than an agreement. Here it is
    *derived* from a term both peers hashed, and there is no other way to obtain
    one — a series that never reached an agreement has no object to ask.
    """

    digest: str
    binding: str

    @property
    def require_bound_scent(self) -> bool:
        """Whether the agreed dialect seals the field into the phase-1 commitment.

        True for :data:`~.fixture.BINDING` and nothing else. The alternative is
        not a laxer rule but a different game, and the downgrade it names is to
        **no scent at all** rather than to scent nobody can check — so this is
        the one question the answer to which decides whether the pheromone layer
        runs at all.
        """
        return self.binding == BINDING


@dataclass(frozen=True, slots=True)
class ScentLock:
    """A proposed or agreed scent model, and the digest that pins it."""

    fixture: ScentFixture
    source_offer: str = SOURCE_OFFER

    def terms(self) -> dict[str, object]:
        """The payload that crosses the wire."""
        return {"scent_model": self.fixture.as_terms(), "source_offer": self.source_offer}

    def digest(self) -> str:
        """SHA-256 over the canonicalised model and example.

        The offer text is excluded deliberately: it is a courtesy, not an
        agreement term, and hashing it would make two teams that agree
        perfectly on the physics fail the lock over a difference in wording.
        """
        return config_sha256({"scent_model": self.fixture.as_terms()})

    def canonical(self) -> bytes:
        """Exactly the bytes the digest is taken over, for the audit log."""
        return canonical_bytes({"scent_model": self.fixture.as_terms()})

    def agreement(self) -> ScentAgreement:
        """What has been settled once a peer has matched this lock exactly.

        Built from *our* terms rather than from theirs on purpose. After
        :func:`disputes` comes back empty the two are the same object of
        agreement, and taking ours means a peer cannot smuggle a term through
        the gate by spelling it in a way that compared equal but reads
        differently downstream.
        """
        return ScentAgreement(digest=self.digest(), binding=self.fixture.binding)


def propose(falloff: Falloff = DEFAULT_FALLOFF) -> ScentLock:
    """Our side of the exchange, built from the live engine."""
    return ScentLock(fixture=build(falloff))


def restate(theirs: dict[str, object]) -> str:
    """The digest their own terms produce, whatever digest they claimed.

    A hash a peer merely asserts is a number; it commits them to nothing unless
    it covers the model travelling with it. Without this, an opponent could
    quote *our* digest over somebody else's physics and pass a comparison of
    digests alone — which is exactly the check a lock is for.

    A malformed model restates over an empty one rather than raising: this is
    the opponent's payload, and a crash on an inbound message is a technical
    loss scoring zero for both sides. :func:`compare` names the malformation.
    """
    model = theirs.get("scent_model")
    return config_sha256({"scent_model": model if isinstance(model, dict) else {}})


def compare(ours: ScentLock, theirs: dict[str, object]) -> list[str]:
    """Name every term on which the two proposals disagree."""
    received = theirs.get("scent_model")
    if not isinstance(received, dict):
        return ["scent_model: missing or malformed"]
    mine = ours.fixture.as_terms()
    problems = []
    for key in sorted(set(mine) | set(received)):
        if key not in received:
            problems.append(f"{key}: absent from their proposal")
        elif key not in mine:
            problems.append(f"{key}: not a term we recognise")
        elif received[key] != mine[key]:
            problems.append(f"{key}: they have {received[key]!r}, we have {mine[key]!r}")
    return problems


def agreed(ours: ScentLock, theirs: dict[str, object]) -> bool:
    """Whether the series may open on this model."""
    return not compare(ours, theirs)


def disputes(ours: ScentLock, theirs: dict[str, object], claimed: str) -> list[str]:
    """Every reason this offer cannot open a series: terms and digest checks."""
    problems = compare(ours, theirs)
    restated = restate(theirs)
    if not digests_agree(restated, claimed):
        problems.append(
            f"scent_sha256: they claim {claimed} over terms that hash to {restated}, "
            "so their digest covers a model they did not send"
        )
    if not digests_agree(ours.digest(), claimed):
        problems.append(f"scent_sha256: they lock {claimed}, we lock {ours.digest()}")
    return problems
