"""Action classifiers and rule matchers for the guardrail system."""

import re
from harness.core.action import Action
from harness.guardrail import Rule


class ActionClassifier:
    """Classify actions into categories based on action name."""

    CATEGORY_MAP = {
        "shell_exec": "shell",
        "shell": "shell",
        "file_read": "file_operation",
        "file_write": "file_operation",
        "file_delete": "file_operation",
        "file_search": "file_operation",
        "file_edit": "file_operation",
    }

    @classmethod
    def classify(cls, action: Action) -> str:
        return cls.CATEGORY_MAP.get(action.name, "general")


class RuleMatcher:
    """Match actions against guardrail rules."""

    @staticmethod
    def match(action: Action, rule: Rule) -> bool:
        """Check if an action matches a given rule."""
        match_spec = rule.match
        if not match_spec:
            return False

        # Check by action name
        if "action" in match_spec:
            if action.name != match_spec["action"]:
                return False

        # Check path patterns (glob patterns)
        if "path" in match_spec:
            path_spec = match_spec["path"]
            params_path = str(action.params.get("path", ""))
            if "patterns" in path_spec:
                if not RuleMatcher._matches_any_glob(params_path, path_spec["patterns"]):
                    return False

        # Check blacklist patterns (regex patterns for shell commands)
        if "blacklist" in match_spec:
            command = action.params.get("command", "")
            return RuleMatcher._matches_any_regex(command, match_spec["blacklist"])

        return True

    @staticmethod
    def _matches_any_glob(text: str, patterns: list[str]) -> bool:
        """Match text against glob-style patterns (e.g. /etc/**)."""
        for pattern in patterns:
            try:
                i = 0
                regex_parts = []
                while i < len(pattern):
                    if pattern[i : i + 3] == "/**":
                        regex_parts.append("/.*")
                        i += 3
                    elif pattern[i : i + 2] == "**":
                        regex_parts.append(".*")
                        i += 2
                    elif pattern[i] == "*":
                        regex_parts.append(r"[^/]*")
                        i += 1
                    elif pattern[i] == "?":
                        regex_parts.append(r"[^/]")
                        i += 1
                    else:
                        regex_parts.append(re.escape(pattern[i]))
                        i += 1
                regex = "".join(regex_parts)
                if re.search(regex, text):
                    return True
            except re.error:
                if pattern in text:
                    return True
        return False

    @staticmethod
    def _matches_any_regex(text: str, patterns: list[str]) -> bool:
        """Match text against regex patterns (e.g. rm\\s+-rf\\s+/)."""
        for pattern in patterns:
            try:
                if re.search(pattern, text):
                    return True
            except re.error:
                if pattern in text:
                    return True
        return False
