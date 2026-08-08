from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestTheAddressBook:
    def test_it_keys_by_role_and_records_reachability(self) -> None:
        book = AddressBook.of(greet("police", PUBLIC_COP), greet("thief", LOCAL_THIEF))
        assert set(book.entries) == {"police", "thief"}
        assert book.entries["police"]["reachable"] is True
        assert book.entries["thief"]["reachable"] is False
    def test_a_pair_is_complete_and_a_single_peer_is_not(self) -> None:
        assert AddressBook.of(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF)).complete
        assert not AddressBook({"police": {}}).complete
    def test_the_fragment_is_sorted_so_two_peers_write_identical_bytes(self) -> None:
        book = AddressBook.of(greet("thief", PUBLIC_THIEF), greet("police", PUBLIC_COP))
        assert list(book.to_fragment()[ADDRESS_KEY]) == ["police", "thief"]
    def test_the_fragment_does_not_alias_the_book(self) -> None:
        book = AddressBook.of(greet("police", PUBLIC_COP), greet("thief", PUBLIC_THIEF))
        book.to_fragment()[ADDRESS_KEY]["police"]["public_url"] = "tampered"
        assert book.entries["police"]["public_url"] == f"{PUBLIC_COP}/mcp"
