"""The report: structured JSON, sent as an attachment, never as prose."""

import base64
import json
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Any

from ..shared.naming import result_filename

LECTURER = "rmisegal+uoh26finalgame@gmail.com"
"""FR-7.17: the mandatory destination, hard-coded and not configurable.

Deliberately not a parameter and not read from config. A configurable
destination is one typo away from a report that was sent, looks sent, and never
arrived — and the failure is indistinguishable from not reporting, which scores
zero for the side that did it.
"""

CONTENT_TYPE = ("application", "json")
SCHEMA_VERSION = "1.0.0"


from ._report_models import (
    ReportError as ReportError,
)
from ._report_models import (
    Repositories as Repositories,
)
from ._report_models import (
    SubGameResult as SubGameResult,
)


@dataclass(frozen=True, slots=True)
class Report:
    """A finished match, ready to be serialised and attached."""

    game_id: str
    role: str
    team: str
    opponent_team: str
    repositories: Repositories
    sub_games: tuple[SubGameResult, ...]
    total_tokens: int
    agreed: bool
    game_uid: str = ""
    started_at: str = ""
    ended_at: str = ""

    def __post_init__(self) -> None:
        if not self.sub_games:
            raise ReportError("a report with no sub-games describes no match")
        numbers = [result.sub_game for result in self.sub_games]
        if len(set(numbers)) != len(numbers):
            raise ReportError(f"sub-game numbers repeat: {numbers}")
        if self.total_tokens < 0:
            raise ReportError(f"total_tokens cannot be negative, got {self.total_tokens}")

    @property
    def cop_total(self) -> int:
        return sum(result.cop_score for result in self.sub_games)

    @property
    def thief_total(self) -> int:
        return sum(result.thief_score for result in self.sub_games)

    def to_dict(self) -> dict[str, Any]:
        """The whole report, as the one structure a parser will read."""
        return {
            "schema_version": SCHEMA_VERSION,
            "game_id": self.game_id,
            "game_uid": self.game_uid,
            "reported_by": {"role": self.role, "team": self.team},
            "opponent_team": self.opponent_team,
            "repositories": self.repositories.to_dict(),
            "sub_games": [result.to_dict() for result in self.sub_games],
            "totals": {
                "cop": self.cop_total,
                "thief": self.thief_total,
                "sub_games_played": len(self.sub_games),
                "total_tokens": self.total_tokens,
            },
            "result_agreed_with_opponent": self.agreed,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }

    def to_json(self) -> str:
        """Sorted keys and a trailing newline, so two peers produce identical bytes."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    @property
    def filename(self) -> str:
        return result_filename(self.game_id)

    def write(self, directory: Path) -> Path:
        """Write ``result_<game_id>.json`` — the same bytes that get attached."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / self.filename
        path.write_text(self.to_json())
        return path


@dataclass
class Message:
    """The mail, with the report as its only payload of record."""

    report: Report
    sender: str
    to: str = LECTURER

    _built: EmailMessage | None = field(default=None, init=False, repr=False)

    def subject(self) -> str:
        return f"[uoh26] {self.report.role} result — {self.report.game_id}"

    def body(self) -> str:
        """What a person reads. Deliberately says nothing a parser would want."""
        return (
            f"Automated match report from the {self.report.role} agent.\n"
            f"The result is the attached {self.report.filename}; this text is not "
            "part of the report and is not machine-readable on purpose.\n"
        )

    def build(self) -> EmailMessage:
        """Assemble the MIME message with the report attached as JSON."""
        mail = EmailMessage()
        mail["To"] = self.to
        mail["From"] = self.sender
        mail["Subject"] = self.subject()
        mail.set_content(self.body())
        mail.add_attachment(
            self.report.to_json().encode("utf-8"),
            maintype=CONTENT_TYPE[0],
            subtype=CONTENT_TYPE[1],
            filename=self.report.filename,
        )
        self._built = mail
        return mail

    def raw(self) -> dict[str, str]:
        """The Gmail API's ``users.messages.send`` body: url-safe base64 MIME."""
        mail = self._built or self.build()
        return {"raw": base64.urlsafe_b64encode(mail.as_bytes()).decode("ascii")}
