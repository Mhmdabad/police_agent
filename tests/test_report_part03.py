from importlib import import_module

globals().update({k: v for k, v in vars(import_module("test_report")).items() if not k.startswith("__")})

class TestAgreementIsRecorded:
    def test_it_says_whether_both_teams_agreed(self) -> None:
        assert json.loads(report().to_json())["result_agreed_with_opponent"] is True
        assert json.loads(report(agreed=False).to_json())["result_agreed_with_opponent"] is False
    def test_a_technical_loss_is_marked_per_sub_game(self) -> None:
        void = SubGameResult(
            sub_game=1, cop_score=0, thief_score=0, commit_hash="abc", technical_loss=True
        )
        assert json.loads(report(sub_games=(void,)).to_json())["sub_games"][0]["technical_loss"]
