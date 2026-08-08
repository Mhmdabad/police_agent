from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_main")).items() if not k.startswith("__")})

class TestWhereWeSayWeAre:
    def test_no_tunnel_is_reported_rather_than_refused(self) -> None:
        assert "not publicly reachable" in where_we_are(NO_TUNNEL, NO_NGROK)
    def test_the_warning_names_what_it_is_not_good_enough_for(self) -> None:
        assert "league match" in where_we_are(NO_TUNNEL, NO_NGROK)
    def test_a_public_url_is_used(self) -> None:
        assert (
            where_we_are_url({"PUBLIC_URL": "https://abc.ngrok.io"}) == "https://abc.ngrok.io/mcp"
        )
    def test_a_loopback_url_that_was_set_on_purpose_is_an_error(self) -> None:
        with pytest.raises(StartupError, match="unusable"):
            where_we_are_url({"PUBLIC_URL": "http://127.0.0.1:8801"})
    def test_the_error_explains_the_cost(self) -> None:
        with pytest.raises(StartupError, match="not reachable from another machine"):
            where_we_are_url({"PUBLIC_URL": "http://localhost:8801"})
