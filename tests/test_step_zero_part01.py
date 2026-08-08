from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestUnknownIsDeclaredAsUnknown:
    def test_an_undetected_gpu_is_null_and_not_zero(self) -> None:
        hardware = collect("claude-haiku-4-5", environ={})
        assert hardware.gpu is None
        assert hardware.vram_mb is None
        assert hardware.to_dict()["vram_mb"] is None
    def test_a_supplied_gpu_is_declared(self) -> None:
        hardware = collect("m", environ={GPU_ENV: "RTX 4070", VRAM_ENV: "8192"})
        assert (hardware.gpu, hardware.vram_mb) == ("RTX 4070", 8192)
    @pytest.mark.parametrize("raw", ["", "  ", "lots", "-1", "0", "8gb", None])
    def test_a_malformed_vram_figure_is_absent_rather_than_fatal(self, raw: str | None) -> None:
        assert _positive_int(raw) is None
    def test_an_empty_gpu_name_is_absent_rather_than_empty(self) -> None:
        assert collect("m", environ={GPU_ENV: ""}).gpu is None
    def test_it_reports_which_fields_need_an_operator(self) -> None:
        hardware = collect("claude-haiku-4-5", environ={})
        assert "gpu" in hardware.undetected
        assert "vram_mb" in hardware.undetected
        assert "os" not in hardware.undetected
