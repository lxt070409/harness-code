import re
from harness.core.action import Action
from harness.guardrail import Rule, Verdict


class ActionClassifier:

    @staticmethod
    def classify(action: Action) -> str:
        """Route action to a rule category based on action name and params."""
        action_to_category = {
            "file_read": "file_operation",
            "file_write": "file_operation",
            "file_delete": "file_operation",
            "file_search": "file_operation",
            "shell_exec": "shell",
            "image_read": "image",
        }
        return action_to_category.get(action.name, "unknown")


class RuleMatcher:

    @staticmethod
    def match(action: Action, rule: Rule) -> bool:
        """Check if an action matches a single rule's conditions."""
        category = rule.category

        if category == "file_operation":
            return _match_file_operation(action, rule)
        elif category == "shell":
            return _match_shell(action, rule)
        else:
            return False


def _match_file_operation(action: Action, rule: Rule) -> bool:
    match = rule.match
    # Check action name match
    if "action" in match and match["action"] != action.name:
        return False

    # Check path patterns
    if "path" in match:
        path_info = match["path"]
        target_path = action.params.get("path", "")

        # Check inclusion patterns
        patterns = path_info.get("patterns", [])
        for pat in patterns:
            if _path_match(target_path, pat):
                # Check exclusion
                excludes = path_info.get("exclude", [])
                for ex in excludes:
                    if _path_match(target_path, ex):
                        return False
                return True

    return False


def _match_shell(action: Action, rule: Rule) -> bool:
    match = rule.match
    command = action.params.get("command", "")

    blacklist = match.get("blacklist", [])
    for pattern in blacklist:
        if re.search(pattern, command, re.IGNORECASE):
            return True

    return False


def _path_match(target: str, pattern: str) -> bool:
    """Simple glob-like path matching. Supports ** and *."""
    # Escape regex special chars, then replace ** and *
    regex = re.escape(pattern)
    regex = regex.replace(r"\*\*", ".*")
    regex = regex.replace(r"\*", "[^/]*")
    regex = f"^{regex}$"
    return bool(re.search(regex, target))
