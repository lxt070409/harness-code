"""Action parser — converts LLM responses into Action objects."""

import json
import re
from harness.core.action import Action


class ActionParser:
    """Parse LLM responses into structured Action objects."""

    @staticmethod
    def parse(response: dict) -> Action:
        """Convert LLM dict response into an Action object."""
        return Action(
            name=response.get("action", ""),
            params=response.get("params", {}),
            rationale=response.get("rationale", ""),
        )

    @staticmethod
    def parse_json(text: str) -> dict | None:
        """
        Parse LLM text response as JSON. Returns None if parsing fails.
        Tries to extract JSON from markdown code blocks as fallback.
        """
        # Try direct parse first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting from ```json ... ``` block
        if "```" in text:
            match = re.search(r"```(?:json)?\s*\n?(.*?)```", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    pass

        return None
