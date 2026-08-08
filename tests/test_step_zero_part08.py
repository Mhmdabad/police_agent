from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestTheProvenanceFragment:
    def test_it_names_every_field_the_rulebook_asks_for(self, tmp_path: Path) -> None:
        fragment = provenance("0.1.0", "s82kma9e", 2, repo=repo(tmp_path)).to_dict()
        assert set(fragment) == {
            "code_version",
            "group_name",
            "sub_game",
            "github_commit",
            "working_tree_dirty",
        }
    def test_it_survives_json(self, tmp_path: Path) -> None:
        fragment = provenance("0.1.0", "s82kma9e", 2, repo=repo(tmp_path)).to_dict()
        assert json.loads(json.dumps(fragment)) == fragment
    def test_it_is_frozen(self, tmp_path: Path) -> None:
        with pytest.raises(AttributeError):
            provenance("0.1.0", "s82kma9e", 1, repo=repo(tmp_path)).sub_game = 9  # type: ignore[misc]
