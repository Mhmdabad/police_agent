from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_handshake")).items() if not k.startswith("__")})

class TestTheDeclarationRecordsWhenAnAddressTookEffect:
    def test_the_sub_game_travels_with_the_book(self) -> None:
        book = AddressBook.peered(opened(4))
        assert {e["since_sub_game"] for e in book.entries.values()} == {4}
    def test_a_rotation_updates_the_file_in_place(self, tmp_path: Path) -> None:
        first = opened()
        record(tmp_path, "g1", AddressBook.peered(first))
        later = first.rotate(greet("police", PUBLIC_COP), greet("thief", ROTATED_THIEF), 2)
        written = json.loads(record(tmp_path, "g1", AddressBook.peered(later)).read_text())
        assert written[ADDRESS_KEY]["thief"]["public_url"] == f"{ROTATED_THIEF}/mcp"
        assert written[ADDRESS_KEY]["thief"]["since_sub_game"] == 2
