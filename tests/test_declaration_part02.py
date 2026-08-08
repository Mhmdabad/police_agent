from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_declaration")).items() if not k.startswith("__")})

class TestItCannotBeBuiltIncomplete:
    def test_a_team_with_no_members(self) -> None:
        with pytest.raises(DeclarationError, match="declares no members"):
            Team(name="x", members=(), cop_repo="a", thief_repo="b")
    def test_a_team_with_no_name(self) -> None:
        with pytest.raises(DeclarationError, match="needs a name"):
            Team(name="", members=("a",), cop_repo="a", thief_repo="b")
    @pytest.mark.parametrize("missing", ["cop_repo", "thief_repo"])
    def test_a_team_missing_a_repository_link(self, missing: str) -> None:
        fields = {"name": "x", "members": ("a",), "cop_repo": "a", "thief_repo": "b"}
        fields[missing] = ""
        with pytest.raises(DeclarationError, match="four repository links"):
            Team(**fields)  # type: ignore[arg-type]
    @pytest.mark.parametrize("missing", ["ours", "theirs"])
    def test_an_empty_mcp_address(self, missing: str) -> None:
        fields = {"ours": "a", "theirs": "b"}
        fields[missing] = ""
        with pytest.raises(DeclarationError, match="MCP address is empty"):
            Endpoints(**fields)
    def test_no_game_uid(self) -> None:
        with pytest.raises(DeclarationError, match="shares a game_uid"):
            declared(game_uid="")
    def test_no_llm_model(self) -> None:
        with pytest.raises(DeclarationError, match="declared LLM model is empty"):
            declared(llm_model="")
    @pytest.mark.parametrize("ceiling", [0, -1])
    def test_a_non_positive_token_ceiling(self, ceiling: int) -> None:
        with pytest.raises(DeclarationError, match="must be positive"):
            declared(token_ceiling=ceiling)
    def test_no_start_time(self) -> None:
        with pytest.raises(DeclarationError, match="fixes nothing in time"):
            declared(started_at="")
    def test_two_teams_with_the_same_name(self) -> None:
        with pytest.raises(DeclarationError, match="both teams are called"):
            declared(them=Team(name="uoh26-cops", members=("x",), cop_repo="a", thief_repo="b"))
