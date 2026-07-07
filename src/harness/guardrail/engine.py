from harness.core.action import Action
from harness.guardrail import Rule, Verdict
from harness.guardrail.classifiers import ActionClassifier, RuleMatcher


class GuardrailEngine:

    def __init__(self, rules: list[Rule] | None = None):
        self.rules = rules or []
        self._build_index()

    def _build_index(self):
        """Group rules by category for faster lookup."""
        self._rules_by_category: dict[str, list[Rule]] = {}
        for rule in self.rules:
            self._rules_by_category.setdefault(rule.category, []).append(rule)

    def evaluate(self, action: Action) -> Verdict:
        """Evaluate an action against all rules. Returns the highest-severity match."""
        category = ActionClassifier.classify(action)
        applicable_rules = self._rules_by_category.get(category, [])

        result = Verdict.ALLOW

        for rule in applicable_rules:
            if RuleMatcher.match(action, rule):
                rule_verdict = self._severity_to_verdict(rule.severity)
                if self._verdict_priority(rule_verdict) > self._verdict_priority(result):
                    result = rule_verdict

        return result

    @staticmethod
    def _severity_to_verdict(severity: str) -> Verdict:
        mapping = {
            "warn": Verdict.ALLOW,
            "block": Verdict.BLOCK,
            "block_always": Verdict.BLOCK_ALWAYS,
        }
        return mapping.get(severity, Verdict.ALLOW)

    @staticmethod
    def _verdict_priority(v: Verdict) -> int:
        return {
            Verdict.ALLOW: 0,
            Verdict.BLOCK: 1,
            Verdict.BLOCK_ALWAYS: 2,
        }.get(v, 0)

    def matched_rule(self, action: Action) -> Rule | None:
        """Return the first matching rule (for audit logging)."""
        category = ActionClassifier.classify(action)
        applicable_rules = self._rules_by_category.get(category, [])
        for rule in applicable_rules:
            if RuleMatcher.match(action, rule):
                return rule
        return None
