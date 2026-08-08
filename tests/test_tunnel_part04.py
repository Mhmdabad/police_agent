from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_tunnel")).items() if not k.startswith("__")})

class TestReadingTheNgrokAgent:
    def test_it_prefers_https_when_the_agent_publishes_both(self) -> None:
        assert from_ngrok(ngrok_body("http://x.ngrok.io", "https://x.ngrok.io")) == (
            "https://x.ngrok.io"
        )
    def test_it_falls_back_to_http(self) -> None:
        assert from_ngrok(ngrok_body("http://x.ngrok.io")) == "http://x.ngrok.io"
    def test_it_accepts_bytes_as_urlopen_returns_them(self) -> None:
        assert from_ngrok(ngrok_body(PUBLIC).encode()) == PUBLIC
    @pytest.mark.parametrize(
        "payload",
        ['{"tunnels": []}', "{}", '{"tunnels": [{"proto": "tcp"}]}', '{"tunnels": null}', "[]"],
    )
    def test_it_refuses_a_response_with_no_usable_tunnel(self, payload: str) -> None:
        with pytest.raises(NotPublicError):
            from_ngrok(payload)
    def test_it_refuses_a_response_that_is_not_json(self) -> None:
        with pytest.raises(NotPublicError, match="no usable JSON"):
            from_ngrok("<html>ngrok is not running</html>")
    def test_it_ignores_a_tcp_tunnel_beside_a_usable_one(self) -> None:
        body = json.dumps(
            {"tunnels": [{"public_url": "tcp://0.tcp.ngrok.io:1"}, {"public_url": PUBLIC}]}
        )
        assert from_ngrok(body) == PUBLIC
    def test_it_fetches_from_the_agents_loopback_api(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seen: dict[str, Any] = {}
        class Response:
            def read(self) -> bytes:
                return b'{"tunnels": []}'
            def __enter__(self) -> "Response":
                return self
            def __exit__(self, *_: object) -> None:
                return None
        def fake(url: str, timeout: float) -> Response:
            seen.update(url=url, timeout=timeout)
            return Response()
        monkeypatch.setattr(urllib.request, "urlopen", fake)
        assert read_ngrok_api() == b'{"tunnels": []}'
        assert seen == {"url": NGROK_API, "timeout": 2.0}
