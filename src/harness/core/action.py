from dataclasses import dataclass, field


@dataclass
class Action:
    name: str
    params: dict = field(default_factory=dict)
    rationale: str = ""

    def describe(self) -> str:
        """Human-readable description for HITL display."""
        return f"[{self.name}] params={self.params} | reason: {self.rationale}"
