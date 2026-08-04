"""Stage 5 acceptance: a full round between two peers on public addresses.

The unit tests prove each piece. This proves the milestone the rulebook states
for stage 5 — *an agent on a remote machine connects through a tunnel and plays
a full round against the local agent* — end to end, with nothing pointing at
loopback.

The opponent here is a second :class:`Orchestrator` constructed with the other
role. It stands in for a remote peer, and it is a **stand-in, not a shortcut**:
the two objects share no state, exchange only serialised dictionaries, and
reach each other exclusively through a transport that routes by URL. If either
side reached into the other, the routing table below would never be consulted
and the test would still pass — which is why the routing is asserted on
directly.

Being able to build both roles in one process is not a separation breach. The
rule forbids the cop and thief *implementations* sharing memory, and this file
imports nothing from the sibling package; ``Orchestrator(role=...)`` is our own
code playing a part.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from cop_agent.infra.handshake import ADDRESS_KEY
from cop_agent.infra.inboxes import PeerInboxes
from cop_agent.infra.mcp_client import OPPONENT_URL_ENV, ClientSettings, OpponentClient
from cop_agent.runtime.orchestrator import MatchAborted, Orchestrator

COP_URL = "https://cop-a1b2.ngrok-free.app/mcp"
THIEF_URL = "https://thief-c3d4.ngrok-free.app/mcp"
MOVED_THIEF_URL = "https://thief-e5f6.ngrok-free.app/mcp"
TURN = {
    "step": 1,
    "sender": "thief",
    "hint": "heading for the water",
    "smell_grid": {"3,3": 0.9},
    "commit": "a" * 64,
    "timestamp": "2026-08-04T09:00:00+00:00",
}


class Internet:
    """Routes calls to whichever peer is listening on a URL.

    The whole point of stage 5: a message is addressed, not handed over. A URL
    nobody is serving raises :class:`ConnectionError`, which is what a dead
    tunnel looks like from the other side.
    """

    def __init__(self) -> None:
        self.hosts: dict[str, Orchestrator] = {}
        self.delivered: list[tuple[str, str]] = []

    def listen(self, url: str, peer: Orchestrator) -> None:
        self.hosts[url] = peer

    def call(self, url: str, tool: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        del timeout
        if url not in self.hosts:
            raise ConnectionError(f"nothing answers at {url}")
        self.delivered.append((url, tool))
        return self.hosts[url].handle_inbound(tool, payload)


def peer(net: Internet, role: str, ours: str, theirs: str) -> Orchestrator:
    settings = ClientSettings.from_config({"opponent_url": theirs}, environ={})
    orchestrator = Orchestrator(PeerInboxes(), OpponentClient(net, settings), role=role)
    net.listen(ours, orchestrator)
    return orchestrator


@pytest.fixture
def wired() -> tuple[Internet, Orchestrator, Orchestrator]:
    net = Internet()
    cop = peer(net, "police", COP_URL, THIEF_URL)
    thief = peer(net, "thief", THIEF_URL, COP_URL)
    return net, cop, thief


class TestAFullRoundOverPublicAddresses:
    def test_both_peers_are_addressed_by_a_public_url(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        """Nothing in the wiring points at loopback."""
        net, _, _ = wired
        assert set(net.hosts) == {COP_URL, THIEF_URL}
        assert not any("127.0.0.1" in url or "localhost" in url for url in net.hosts)

    def test_the_handshake_completes_and_the_declaration_names_both(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        ours, theirs = cop.greeting(COP_URL, "s82kma9e"), thief.greeting(THIEF_URL, "them")
        cop.announce(ours)
        thief.announce(theirs)

        peering = cop.open_series(ours, tmp_path, "uoh26-s82kma9e")
        assert peering.sub_game == 1
        written = json.loads((tmp_path / "declaration_uoh26-s82kma9e.json").read_text())
        assert written[ADDRESS_KEY]["police"]["public_url"] == COP_URL
        assert written[ADDRESS_KEY]["thief"]["public_url"] == THIEF_URL
        assert all(entry["reachable"] for entry in written[ADDRESS_KEY].values())

    def test_a_turn_crosses_the_network_and_lands_in_the_mailbox(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        net, cop, thief = wired
        assert thief.call_opponent("receive_turn", TURN)["ok"] is True
        assert net.delivered == [(COP_URL, "receive_turn")]
        assert cop.inboxes.turns.get_nowait().hint == "heading for the water"

    def test_a_full_round_completes_with_no_loopback_traffic(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        """The stage 5 milestone: handshake, then turns, over public addresses."""
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")

        for step in range(1, 6):
            assert thief.call_opponent("receive_turn", {**TURN, "step": step})["ok"] is True
            assert cop.inboxes.turns.get_nowait().step == step

        assert [url for url, _ in net.delivered] == [COP_URL, THIEF_URL] + [COP_URL] * 5

    def test_a_dropped_tunnel_is_a_recorded_abort_rather_than_a_hang(
        self, wired: tuple[Internet, Orchestrator, Orchestrator]
    ) -> None:
        """A URL nobody serves is exactly what a dead tunnel looks like.

        The retry budget is spent and the result is a named cause. A technical
        loss scores zero for both sides, but only a *named* one can be agreed
        and reported — and agreement is required before either team may send
        its result.
        """
        net, cop, _ = wired
        del net.hosts[THIEF_URL]
        with pytest.raises(MatchAborted, match="nothing answers|after 4 attempts"):
            cop.call_opponent("receive_turn", TURN)


class TestSurvivingATunnelRestartMidSeries:
    """The stage 5 milestone: a new URL between sub-games, no restart."""

    def test_the_series_continues_at_the_new_address(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        assert cop.call_opponent("receive_turn", TURN)["ok"] is True

        # The thief's free-tier tunnel is recycled between sub-games.
        del net.hosts[THIEF_URL]
        net.listen(MOVED_THIEF_URL, thief)
        thief.announce(thief.greeting(MOVED_THIEF_URL, "them"))

        second = cop.rehandshake(first, cop.greeting(COP_URL, "s82kma9e"), 2, tmp_path, "g1")
        assert second.theirs.public_url == MOVED_THIEF_URL
        assert cop.call_opponent("receive_turn", {**TURN, "step": 2})["ok"] is True
        assert net.delivered[-1] == (MOVED_THIEF_URL, "receive_turn")

    def test_without_the_re_handshake_the_old_address_is_dead(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        """What the re-handshake is worth: the whole series, not one sub-game.

        A technical loss scores zero for **both** sides, so a tunnel recycled
        partway through destroys sub-games already won on the board.
        """
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")

        del net.hosts[THIEF_URL]
        net.listen(MOVED_THIEF_URL, thief)
        with pytest.raises(MatchAborted):
            cop.call_opponent("receive_turn", TURN)

    def test_the_declaration_says_which_sub_game_the_move_took_effect(
        self, wired: tuple[Internet, Orchestrator, Orchestrator], tmp_path: Path
    ) -> None:
        net, cop, thief = wired
        thief.announce(thief.greeting(THIEF_URL, "them"))
        first = cop.open_series(cop.greeting(COP_URL, "s82kma9e"), tmp_path, "g1")
        net.listen(MOVED_THIEF_URL, thief)
        thief.announce(thief.greeting(MOVED_THIEF_URL, "them"))
        cop.rehandshake(first, cop.greeting(COP_URL, "s82kma9e"), 2, tmp_path, "g1")

        written = json.loads((tmp_path / "declaration_g1.json").read_text())
        assert written[ADDRESS_KEY]["thief"]["since_sub_game"] == 2
        assert written[ADDRESS_KEY]["police"]["public_url"] == COP_URL


class TestConfiguringTheRemotePeer:
    def test_the_committed_config_is_overridden_for_league_play(self) -> None:
        """One exported variable turns a local run into a remote one."""
        local = ClientSettings.from_config({"opponent_url": "http://127.0.0.1:8802/mcp"}, {})
        remote = ClientSettings.from_config(
            {"opponent_url": "http://127.0.0.1:8802/mcp"}, {OPPONENT_URL_ENV: THIEF_URL}
        )
        assert local.opponent_url == "http://127.0.0.1:8802/mcp"
        assert remote.opponent_url == THIEF_URL
