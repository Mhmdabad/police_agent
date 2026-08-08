from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_artefacts")).items() if not k.startswith("__")})

class TestEverythingIsReportedAtOnce:
    def test_several_problems_come_back_together(self) -> None:
        broken = a_set(
            configs=(a_config(1, uid="u-9"), a_config(2, uid="u-9")),
            result=a_result(uid="u-8"),
        )
        assert len(broken.check().problems) >= 3
    def test_the_summary_lists_them(self) -> None:
        broken = a_set(result=a_result(uid="u-8"))
        assert str(broken.check()).startswith("the artefacts disagree:")
