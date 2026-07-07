from harness.core.action import Action
from harness.guardrail.hitl import HITLPipeline


class TestHITLPipeline:

    def test_approve_flow(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "y")
        action = Action("shell_exec", {"command": "rm -rf /"}, "cleanup")
        result = HITLPipeline.prompt(action)
        assert result is True, f"Expected True (approved), got {result}"

    def test_deny_flow(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "n")
        action = Action("shell_exec", {"command": "rm -rf /"}, "cleanup")
        result = HITLPipeline.prompt(action)
        assert result is False, f"Expected False (denied), got {result}"

    def test_default_no(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _: "")
        action = Action("shell_exec", {"command": "rm -rf /"}, "cleanup")
        result = HITLPipeline.prompt(action)
        assert result is False, f"Expected False (default), got {result}"

    def test_max_retries(self, monkeypatch):
        inputs = iter(["invalid", "bad", "???"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs))
        action = Action("shell_exec", {"command": "rm -rf /"}, "cleanup")
        result = HITLPipeline.prompt(action)
        assert result is False, f"Expected False after max retries, got {result}"
