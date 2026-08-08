from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_rehandshake_between_subgames")).items() if not k.startswith("__")})

def test_a_free_port_is_actually_free() -> None:
    port = free_port()
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))
