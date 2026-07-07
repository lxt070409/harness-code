import re
import yaml
from pathlib import Path
from harness.guardrail import Rule


class RuleLoader:

    @staticmethod
    def load(path: str | Path) -> list[Rule]:
        path = Path(path)
        if not path.exists():
            return _default_rules()

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "rules" not in data:
            return _default_rules()

        return [Rule(**r) for r in data["rules"]]


def _default_rules() -> list[Rule]:
    return [
        Rule(id="default-rm-rf", category="shell", severity="block",
             description="Block rm -rf /", match={"blacklist": [r"rm\s+-rf\s+/"]}),
        Rule(id="default-etc-write", category="file_operation", severity="block_always",
             description="Never write to /etc/passwd",
             match={"action": "file_write", "path": {"patterns": ["/etc/passwd"]}}),
    ]
