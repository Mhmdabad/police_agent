from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_peer")).items() if not k.startswith("__")})

class TestASilentOpponent:
    def test_a_missing_commitment_is_a_timeout(self) -> None:
        peer, _, _ = a_peer()
        with pytest.raises(PeerTimeout, match="commitment for step 1"):
            peer.await_commit(1)
    def test_a_missing_reveal_is_a_timeout(self) -> None:
        peer, _, _ = a_peer()
        with pytest.raises(PeerTimeout, match="audit record"):
            peer.await_reveal(1)
    def test_a_missing_final_reveal_is_a_timeout(self) -> None:
        peer, _, _ = a_peer()
        with pytest.raises(PeerTimeout, match="audit record"):
            peer.await_final()
    def test_the_message_says_what_a_silence_costs(self) -> None:
        peer, _, _ = a_peer()
        with pytest.raises(PeerTimeout, match="zero for both sides"):
            peer.await_commit(1)
