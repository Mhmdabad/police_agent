from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_bucket")).items() if not k.startswith("__")})

class TestTheseAreRateTokensAndNothingElse:
    def test_the_module_has_no_notion_of_llm_or_oauth_tokens(self) -> None:
        from cop_agent.infra import token_bucket
        body = Path(str(token_bucket.__file__)).read_text()
        assert "refresh_token" not in body
        assert "token_budget" not in body
