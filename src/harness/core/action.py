from dataclasses import dataclass


@dataclass
class Action:
    name: str
    params: dict
    rationale: str

    def describe(self) -> str:
        return f"{self.name}({self.params})"
