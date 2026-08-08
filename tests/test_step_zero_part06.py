from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_step_zero")).items() if not k.startswith("__")})

class TestHardwareDirectly:
    def test_undetected_is_computed_from_the_fragment(self) -> None:
        bare = Hardware(
            os_name="Linux",
            logical_cores=None,
            cpu_max_mhz=None,
            ram_mb=None,
            gpu=None,
            vram_mb=None,
            llm_model="template",
        )
        assert set(bare.undetected) == {"logical_cores", "cpu_max_mhz", "ram_mb", "gpu", "vram_mb"}
    def test_a_fully_known_machine_has_nothing_undetected(self) -> None:
        full = Hardware("Linux", 8, 3600.0, 16384, "RTX 4070", 8192, "claude-haiku-4-5")
        assert full.undetected == ()
