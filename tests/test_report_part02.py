from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestTheMandatoryFieldsAreRequiredNotValidated:
    def test_all_four_repository_links_are_required(self) -> None:
        with pytest.raises(ReportError, match="four repository links"):
            Repositories(
                cop_repo="https://github.com/Mhmdabad/police_agent",
                thief_repo="",
                opponent_cop_repo="https://github.com/other/police",
                opponent_thief_repo="https://github.com/other/thief",
            )
    def test_the_four_links_reach_the_json(self) -> None:
        links = json.loads(report().to_json())["repositories"]
        assert len(links) == 4
        assert all(links.values())
    def test_every_sub_game_needs_a_commit_hash(self) -> None:
        with pytest.raises(ReportError, match="no commit hash"):
            SubGameResult(sub_game=1, cop_score=0, thief_score=0, commit_hash="")
    def test_the_commit_hashes_reach_the_json(self) -> None:
        played = json.loads(report().to_json())["sub_games"]
        assert [entry["commit_hash"] for entry in played] == [f"{1:040x}", f"{2:040x}"]
    def test_total_tokens_reaches_the_json(self) -> None:
        assert json.loads(report().to_json())["totals"]["total_tokens"] == 41_233
    def test_a_negative_token_total_is_refused(self) -> None:
        with pytest.raises(ReportError, match="cannot be negative"):
            report(total_tokens=-1)
    def test_sub_games_are_numbered_from_one(self) -> None:
        with pytest.raises(ReportError, match="numbered from 1"):
            SubGameResult(sub_game=0, cop_score=0, thief_score=0, commit_hash="abc")
    def test_a_report_with_no_sub_games_is_refused(self) -> None:
        with pytest.raises(ReportError, match="describes no match"):
            report(sub_games=())
    def test_repeated_sub_game_numbers_are_refused(self) -> None:
        with pytest.raises(ReportError, match="numbers repeat"):
            report(sub_games=(result(1), result(1)))
