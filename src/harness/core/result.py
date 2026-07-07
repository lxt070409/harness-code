from dataclasses import dataclass


@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None = None
    signal: str = "continue"  # "continue" | "done" | "error"
