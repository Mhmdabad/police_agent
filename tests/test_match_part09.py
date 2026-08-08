from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_match")).items() if not k.startswith("__")})

class TestReadingTheConfigForAMatch:
    def test_a_start_cell_arrives_from_json_as_a_list(self) -> None:
        assert _cell([3, 4], (0, 0)) == (3, 4)
    def test_a_tuple_survives_unchanged(self) -> None:
        assert _cell((1, 2), (0, 0)) == (1, 2)
    @pytest.mark.parametrize("bad", [None, [1], [1, 2, 3], "3,4", 7])
    def test_anything_unusable_falls_back_rather_than_crashing(self, bad: object) -> None:
        assert _cell(bad, (9, 9)) == (9, 9)
    def test_our_side_is_read_from_the_game_section(self) -> None:
        team = _us(
            {
                "game": {
                    "group_name": "uoh26-cops",
                    "members": ["A", "B"],
                    "repos": {"cop": "https://x/cop", "thief": "https://x/thief"},
                }
            }
        )
        assert team.name == "uoh26-cops"
        assert team.members == ("A", "B")
        assert team.cop_repo == "https://x/cop"
    def test_the_opponent_is_read_from_teams_them(self) -> None:
        team = _them(
            {
                "teams": {
                    "them": {
                        "group_name": "uoh26-others",
                        "members": ["C"],
                        "repos": {"cop": "https://y/cop", "thief": "https://y/thief"},
                    }
                }
            }
        )
        assert team.name == "uoh26-others"
        assert team.thief_repo == "https://y/thief"
    def test_a_team_with_no_repository_links_is_refused(self) -> None:
        from cop_agent.infra.declaration import DeclarationError
        with pytest.raises(DeclarationError, match="four repository links"):
            _us({"game": {"group_name": "x", "members": ["A"]}})
    def test_a_team_with_no_members_is_refused(self) -> None:
        from cop_agent.infra.declaration import DeclarationError
        with pytest.raises(DeclarationError, match="declares no members"):
            _us({"game": {"group_name": "x", "members": [], "repos": {"cop": "c", "thief": "t"}}})
    def test_the_shipped_config_builds_both_teams(self) -> None:
        from cop_agent.__main__ import CONFIG, load_private
        private = load_private(REPO / CONFIG)
        for side in (_us(private), _them(private)):
            assert side.name and side.members
            assert side.cop_repo.startswith("http")
            assert side.thief_repo.startswith("http")
    def test_the_timestamp_is_utc_and_to_the_second(self) -> None:
        from datetime import datetime
        stamp = _now()
        parsed = datetime.fromisoformat(stamp)
        assert parsed.tzinfo is not None
        assert parsed.microsecond == 0
