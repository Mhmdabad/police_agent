"""``declaration_<game_id>.json`` — fixed pre-game parameters and match declaration."""

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from ..shared.naming import declaration_filename
from ._declaration_models import (
    DeclarationError as DeclarationError,
)
from ._declaration_models import (
    Endpoints as Endpoints,
)
from ._declaration_models import (
    Team as Team,
)
from .step_zero import Hardware, Provenance, sign, statement


@dataclass(frozen=True, slots=True)
class MatchDeclaration:
    """The pre-game declaration, ready to sign and write."""

    game_id: str
    game_uid: str
    role: str
    us: Team
    them: Team
    endpoints: Endpoints
    hardware: Hardware
    provenance: Provenance
    llm_model: str
    token_ceiling: int
    started_at: str
    ended_at: str = ""
    signature: str = ""

    def __post_init__(self) -> None:
        if not self.game_uid:
            raise DeclarationError("every artefact of a match shares a game_uid; this has none")
        if not self.llm_model:
            raise DeclarationError(
                "the declared LLM model is empty; it is one of the things the "
                "declaration exists to fix before anybody sees a result"
            )
        if self.token_ceiling <= 0:
            raise DeclarationError(
                f"the agreed token ceiling must be positive, got {self.token_ceiling}"
            )
        if not self.started_at:
            raise DeclarationError("a declaration with no start time fixes nothing in time")
        if self.us.name == self.them.name:
            raise DeclarationError(f"both teams are called {self.us.name!r}")

    @property
    def repositories(self) -> dict[str, str]:
        """All four links, flat, the way the result file wants them."""
        return {
            "cop_repo": self.us.cop_repo,
            "thief_repo": self.us.thief_repo,
            "opponent_cop_repo": self.them.cop_repo,
            "opponent_thief_repo": self.them.thief_repo,
        }

    def content(self) -> dict[str, Any]:
        """Everything the signature covers. Never includes the signature."""
        return {
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "declared_by": self.role,
            "teams": {"us": self.us.to_dict(), "them": self.them.to_dict()},
            "repositories": self.repositories,
            "mcp_addresses": self.endpoints.to_dict(),
            "machine": statement(self.hardware, self.provenance),
            "llm_model": self.llm_model,
            "token_ceiling": self.token_ceiling,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.content(), "signature": self.signature}

    @property
    def filename(self) -> str:
        return declaration_filename(self.game_id)

    def concluded(self, ended_at: str, key: str | None) -> "MatchDeclaration":
        """A copy with the end time filled in, re-signed."""
        if not ended_at:
            raise DeclarationError("concluded() needs an end time")
        return declare_match(replace(self, ended_at=ended_at, signature=""), key)

    def write(self, directory: Path) -> Path:
        """Write ``declaration_<game_id>.json``, sorted, with a trailing newline."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self.filename
        path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n")
        return path


def declare_match(declaration: MatchDeclaration, key: str | None) -> MatchDeclaration:
    """Sign a declaration with the Step-0 key, or mark it unsigned."""
    return replace(declaration, signature=sign(declaration.content(), key))


def build(
    *,
    game_id: str,
    game_uid: str,
    role: str,
    us: Team,
    them: Team,
    endpoints: Endpoints,
    hardware: Hardware,
    provenance: Provenance,
    llm_model: str,
    token_ceiling: int,
    started_at: str,
    key: str | None = None,
) -> MatchDeclaration:
    """Assemble and sign a declaration in one call."""
    return declare_match(
        MatchDeclaration(
            game_id=game_id,
            game_uid=game_uid,
            role=role,
            us=us,
            them=them,
            endpoints=endpoints,
            hardware=hardware,
            provenance=provenance,
            llm_model=llm_model,
            token_ceiling=token_ceiling,
            started_at=started_at,
        ),
        key,
    )
