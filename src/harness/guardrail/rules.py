"""Rule loader — loads guardrail rules from YAML files."""

from pathlib import Path
from harness.guardrail import Rule

try:
    import yaml
except ImportError:
    yaml = None


class RuleLoader:
    """Load guardrail rules from YAML configuration files."""

    @staticmethod
    def load(path: str | Path) -> list[Rule]:
        """Load rules from a YAML file. Returns an empty list if PyYAML is not installed."""
        path = Path(path)
        if not path.exists():
            return []

        if yaml is None:
            # Fallback: return empty list if PyYAML unavailable
            return []

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "rules" not in data:
            return []

        rules = []
        for entry in data["rules"]:
            rules.append(
                Rule(
                    id=entry.get("id", ""),
                    category=entry.get("category", "general"),
                    severity=entry.get("severity", "warn"),
                    description=entry.get("description", ""),
                    match=entry.get("match", {}),
                )
            )
        return rules
