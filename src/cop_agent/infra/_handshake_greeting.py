"""Greeting, Peering, and handshake check functions."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from .protocol import ROLES
from .tunnel import NotPublicError, host_is_public, normalise
from .validation import InvalidPayloadError, require_mapping, require_str


class HandshakeError(ValueError):
    """Raised when the greeting we were sent cannot be played against."""


@dataclass(frozen=True, slots=True)
class Greeting:
    """What one peer tells the other before the series starts."""

    role: str
    group_id: str
    public_url: str
    protocol_version: str

    def __post_init__(self) -> None:
        if self.role not in ROLES:
            raise HandshakeError(f"role must be one of {sorted(ROLES)}, got {self.role!r}")
        if not self.group_id.strip():
            raise HandshakeError("group_id must be set; it identifies the team in the declaration")
        try:
            object.__setattr__(self, "public_url", normalise(self.public_url))
        except NotPublicError as exc:
            raise HandshakeError(str(exc)) from exc

    @property
    def reachable(self) -> bool:
        return host_is_public(urlparse(self.public_url).hostname or "")

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "group_id": self.group_id,
            "public_url": self.public_url,
            "protocol_version": self.protocol_version,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Greeting":
        try:
            body = require_mapping(data, "greeting")
            return cls(
                role=require_str(body, "role"),
                group_id=require_str(body, "group_id"),
                public_url=require_str(body, "public_url"),
                protocol_version=require_str(body, "protocol_version"),
            )
        except InvalidPayloadError as exc:
            raise HandshakeError(str(exc)) from exc


def check(ours: Greeting, theirs: Greeting) -> None:
    if theirs.protocol_version != ours.protocol_version:
        raise HandshakeError(
            f"opponent speaks protocol {theirs.protocol_version!r}, we speak "
            f"{ours.protocol_version!r}; the wire contract must match exactly"
        )
    if theirs.role == ours.role:
        raise HandshakeError(
            f"both peers claim the role {theirs.role!r}; a game with two "
            f"{theirs.role}s has no capture target and no way to end"
        )
    if ours.reachable and not theirs.reachable:
        raise HandshakeError(
            f"we advertise {ours.public_url} but were given {theirs.public_url}, "
            "which routes nowhere from here."
        )


def check_rotation(current: Greeting, fresh: Greeting) -> None:
    for field, was, now in (
        ("role", current.role, fresh.role),
        ("group_id", current.group_id, fresh.group_id),
        ("protocol_version", current.protocol_version, fresh.protocol_version),
    ):
        if was != now:
            raise HandshakeError(
                f"a rotated tunnel may change the address and nothing else, but "
                f"{field} went from {was!r} to {now!r}; this is a different peer"
            )


@dataclass(frozen=True, slots=True)
class Peering:
    """The two addresses in force, and the sub-game they were agreed for."""

    ours: Greeting
    theirs: Greeting
    sub_game: int

    def rotate(self, ours: Greeting, theirs: Greeting, sub_game: int) -> "Peering":
        if sub_game <= self.sub_game:
            raise HandshakeError(
                f"addresses may only change between sub-games; sub-game {sub_game} "
                f"does not follow {self.sub_game}."
            )
        check_rotation(self.ours, ours)
        check_rotation(self.theirs, theirs)
        check(ours, theirs)
        return Peering(ours, theirs, sub_game)

    def relocations(self, later: "Peering") -> dict[str, tuple[str, str]]:
        return {
            was.role: (was.public_url, now.public_url)
            for was, now in ((self.ours, later.ours), (self.theirs, later.theirs))
            if was.public_url != now.public_url
        }
