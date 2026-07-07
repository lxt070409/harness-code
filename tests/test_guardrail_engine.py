import yaml
from pathlib import Path
from harness.core.action import Action
from harness.guardrail import Verdict
from harness.guardrail.engine import GuardrailEngine
from harness.guardrail.rules import RuleLoader


def load_test_rules():
    path = Path(__file__).parent / "fixture" / "sample_rules.yaml"
    return RuleLoader.load(path)


class TestGuardrailShellCommands:

    def setup_method(self):
        self.engine = GuardrailEngine(rules=load_test_rules())

    def test_rm_rf_root_blocked(self):
        action = Action("shell_exec", {"command": "rm -rf /"}, "cleanup")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"

    def test_ls_allowed(self):
        action = Action("shell_exec", {"command": "ls -la"}, "list files")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.ALLOW, f"Expected ALLOW, got {verdict}"

    def test_dd_blocked(self):
        action = Action("shell_exec", {"command": "dd if=/dev/zero of=/dev/sda bs=4M"}, "")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"

    def test_git_force_push_blocked(self):
        action = Action("shell_exec", {"command": "git push --force origin main"}, "update remote")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"

    def test_git_push_allowed(self):
        action = Action("shell_exec", {"command": "git push origin main"}, "update remote")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.ALLOW, f"Expected ALLOW, got {verdict}"

    def test_pip_unknown_blocked(self):
        action = Action("shell_exec", {"command": "pip install unknown-pkg-xyz"}, "install dep")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"

    def test_pip_known_allowed(self):
        action = Action("shell_exec", {"command": "pip install requests"}, "install dep")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.ALLOW, f"Expected ALLOW, got {verdict}"


class TestGuardrailFileOperations:

    def setup_method(self):
        self.engine = GuardrailEngine(rules=load_test_rules())

    def test_delete_etc_blocked(self):
        action = Action("file_delete", {"path": "/etc/passwd"}, "clean")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"

    def test_delete_temp_warn(self):
        action = Action("file_delete", {"path": "/tmp/test.txt"}, "clean")
        verdict = self.engine.evaluate(action)
        # warn severity -> not BLOCK or BLOCK_ALWAYS
        assert verdict not in (Verdict.BLOCK, Verdict.BLOCK_ALWAYS), f"Expected non-block, got {verdict}"

    def test_write_etc_passwd_block_always(self):
        action = Action("file_write", {"path": "/etc/passwd", "content": "hacker"}, "update")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.BLOCK_ALWAYS, f"Expected BLOCK_ALWAYS, got {verdict}"

    def test_no_match_allowed(self):
        action = Action("file_read", {"path": "/tmp/foo.txt"}, "read")
        verdict = self.engine.evaluate(action)
        assert verdict == Verdict.ALLOW, f"Expected ALLOW, got {verdict}"
