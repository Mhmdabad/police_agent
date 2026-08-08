from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestThereIsNoFreeTextPath:
    def test_the_module_offers_no_way_to_send_a_prose_report(self) -> None:
        source = (Path(cop_agent.__file__).parent / "infra" / "report.py").read_text()
        for smell in ("set_content(report", "plain_text", "as_text", "send_text"):
            assert smell not in source, f"a free-text path appeared: {smell}"
    def test_the_only_attachment_type_is_json(self) -> None:
        from cop_agent.infra.report import CONTENT_TYPE
        assert CONTENT_TYPE == ("application", "json")
    def test_the_destination_is_not_configurable_from_outside(self) -> None:
        source = (Path(cop_agent.__file__).parent / "infra" / "report.py").read_text()
        assert 'LECTURER = "rmisegal+uoh26finalgame@gmail.com"' in source
        assert "getenv" not in source and "environ" not in source
