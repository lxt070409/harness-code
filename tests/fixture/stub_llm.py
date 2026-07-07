from harness.core.action import Action


class StubLLM:
    """Mock LLM that returns preset action responses. No network, no real API."""

    def __init__(self, responses: list[dict]):
        self.responses = responses
        self.call_count = 0

    def chat(self, context: str) -> dict:
        if self.call_count >= len(self.responses):
            return {"action": "done", "params": {}, "rationale": "all actions exhausted"}
        resp = self.responses[self.call_count]
        self.call_count += 1
        return resp

    def to_action(self, response: dict) -> Action:
        return Action(
            name=response.get("action", ""),
            params=response.get("params", {}),
            rationale=response.get("rationale", ""),
        )
