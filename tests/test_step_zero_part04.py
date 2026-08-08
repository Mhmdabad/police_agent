from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestTheDeclarationFragment:
    def test_it_names_every_field_the_rulebook_asks_for(self) -> None:
        fields = set(collect("m", environ={}).to_dict())
        assert fields == {
            "os",
            "logical_cores",
            "cpu_max_mhz",
            "ram_mb",
            "gpu",
            "vram_mb",
            "llm_model",
        }
    def test_it_survives_json_because_it_is_going_into_a_signed_file(self) -> None:
        fragment = collect("m", environ={GPU_ENV: "RTX 4070", VRAM_ENV: "8192"}).to_dict()
        assert json.loads(json.dumps(fragment)) == fragment
    def test_it_describes_the_machine_it_is_running_on(self) -> None:
        hardware = collect("m", environ={})
        assert hardware.os_name
        assert hardware.logical_cores is None or hardware.logical_cores >= 1
    def test_it_is_frozen_so_a_declared_machine_cannot_change(self) -> None:
        with pytest.raises(AttributeError):
            collect("m", environ={}).llm_model = "something-else"  # type: ignore[misc]
    def test_nothing_is_probed_at_import_time(self) -> None:
        source = (Path(__file__).parents[1] / "src/cop_agent/infra/step_zero.py").read_text()
        module = ast.parse(source)
        calls = [
            node
            for node in module.body
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)
        ]
        assert calls == []
