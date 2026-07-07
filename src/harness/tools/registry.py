from harness.core.action import Action
from harness.core.result import ToolResult
from harness.tools import Tool


class ToolRegistry:

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        self._tools[tool.name] = tool

    def dispatch(self, action: Action) -> ToolResult:
        if action.name not in self._tools:
            return ToolResult(ok=False, output="", error=f"Tool '{action.name}' not found", signal="error")

        tool = self._tools[action.name]
        try:
            result = tool.func(**action.params)
            return result
        except Exception as e:
            return ToolResult(ok=False, output="", error=str(e), signal="error")

    def describe_tools(self) -> str:
        lines = ["Available tools:"]
        for name, tool in self._tools.items():
            params_str = ", ".join(p if isinstance(p, str) else str(p) for p in tool.parameters) if tool.parameters else ""
            lines.append(f"\n  {tool.name}({params_str})")
            lines.append(f"    {tool.description}")
            if tool.danger_level in ("sensitive", "dangerous"):
                lines.append(f"    ⚠️  {tool.danger_level.upper()}")
        return "\n".join(lines)