from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_token_store")).items() if not k.startswith("__")})

class TestTheRoleIsWhatCatchesACopiedToken:
    def test_a_token_from_the_other_agent_is_refused(self, tmp_path: Path) -> None:
        path = stored(tmp_path, declared_role="thief")
        with pytest.raises(TokenError, match="authorized by the thief agent"):
            read(path, CLIENT, role="police")
    def test_the_message_says_why_the_client_id_did_not_help(self, tmp_path: Path) -> None:
        path = stored(tmp_path, declared_role="thief")
        with pytest.raises(TokenError, match="share one OAuth client"):
            read(path, CLIENT, role="police")
    def test_the_matching_role_is_accepted(self, tmp_path: Path) -> None:
        token = read(stored(tmp_path, declared_role="police"), CLIENT, role="police")
        assert token.role == "police"
    def test_a_caller_that_does_not_care_still_loads_it(self, tmp_path: Path) -> None:
        assert read(stored(tmp_path, declared_role="thief"), CLIENT).role == "thief"
    def test_a_token_written_before_this_field_existed_still_loads(self, tmp_path: Path) -> None:
        assert read(stored(tmp_path), CLIENT, role="police").role == ""
    def test_the_client_id_check_cannot_catch_this(self, tmp_path: Path) -> None:
        copied = stored(tmp_path, declared_role="thief")
        read(copied, CLIENT)  # same client_id, so the earlier check is satisfied
        with pytest.raises(TokenError):
            read(copied, CLIENT, role="police")
