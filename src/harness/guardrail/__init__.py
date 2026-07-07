from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class Verdict(Enum):
    ALLOW = "allow"
    BLOCK = "block"
    BLOCK_ALWAYS = "block_always"


@dataclass
class Rule:
    id: str
    category: str
    severity: str  # "warn" | "block" | "block_always"
    description: str
    match: dict = field(default_factory=dict)
