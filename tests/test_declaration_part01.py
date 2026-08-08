from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_declaration")).items() if not k.startswith("__")})

class TestItFixesEverythingThatDoesNotChange:
    def test_all_four_repository_links_are_present(self) -> None:
        links = declared().content()["repositories"]
        assert len(links) == 4
        assert all(links.values())
        assert links["opponent_thief_repo"] == "https://github.com/other/thief"
    def test_both_teams_and_their_members(self) -> None:
        teams = declared().content()["teams"]
        assert teams["us"]["members"] == ["Mohammed Abad"]
        assert teams["them"]["members"] == ["A Person", "Another"]
    def test_the_mcp_addresses(self) -> None:
        assert declared().content()["mcp_addresses"]["theirs"] == "https://b.ngrok.io/mcp"
    def test_the_hardware_and_the_model(self) -> None:
        content = declared().content()
        assert content["machine"]["hardware"]["ram_mb"] == 16384
        assert content["llm_model"] == "claude-haiku-4-5"
    def test_the_agreed_token_ceiling(self) -> None:
        assert declared().content()["token_ceiling"] == 200_000
    def test_the_commit_the_code_came_from(self) -> None:
        assert declared().content()["machine"]["provenance"]["github_commit"] == "a" * 40
    def test_the_start_time(self) -> None:
        assert declared().content()["started_at"] == "2026-08-05T12:00:00Z"
