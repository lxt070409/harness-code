from dataclasses import dataclass, field
from collections.abc import Callable


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    parameters: list = field(default_factory=list)
    danger_level: str = "safe"  # "safe" | "sensitive" | "dangerous"
