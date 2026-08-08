from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestNormalising:
    def test_it_appends_the_mcp_path_a_tunnel_never_prints(self) -> None:
        assert normalise(PUBLIC) == f"{PUBLIC}{MCP_PATH}"
    def test_it_keeps_a_path_that_is_already_there(self) -> None:
        assert normalise(f"{PUBLIC}/custom") == f"{PUBLIC}/custom"
    def test_it_drops_a_trailing_slash_so_two_peers_agree_on_one_string(self) -> None:
        assert normalise(f"{PUBLIC}/") == f"{PUBLIC}{MCP_PATH}"
    def test_it_strips_query_and_fragment(self) -> None:
        assert normalise(f"{PUBLIC}/mcp?token=x#frag") == f"{PUBLIC}{MCP_PATH}"
    def test_it_tolerates_the_whitespace_a_copy_paste_brings(self) -> None:
        assert normalise(f"  {PUBLIC}\n") == f"{PUBLIC}{MCP_PATH}"
    @pytest.mark.parametrize("raw", ["ftp://x.example", "a1b2.ngrok-free.app", "ws://x.example"])
    def test_it_refuses_a_scheme_fastmcp_does_not_serve(self, raw: str) -> None:
        with pytest.raises(NotPublicError):
            normalise(raw)
    def test_it_refuses_a_url_with_no_host(self) -> None:
        with pytest.raises(NotPublicError, match="no host"):
            normalise("https:///mcp")
