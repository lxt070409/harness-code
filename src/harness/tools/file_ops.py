"""File operation tools for the agent."""

from pathlib import Path
from harness.core.result import ToolResult


def file_read(path: str) -> ToolResult:
    """Read the contents of a file."""
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(ok=False, output="", error=f"File not found: {path}")
        content = p.read_text(encoding="utf-8")
        return ToolResult(ok=True, output=content)
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_write(path: str, content: str) -> ToolResult:
    """Write content to a file."""
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, output=f"Written {len(content)} bytes to {path}")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_delete(path: str) -> ToolResult:
    """Delete a file."""
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(ok=False, output="", error=f"File not found: {path}")
        p.unlink()
        return ToolResult(ok=True, output=f"Deleted {path}")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_search(pattern: str = "", target: str = "content", path: str = ".", name: str = "", **kwargs) -> ToolResult:
    """Search files by content or name pattern."""
    # Support both 'pattern' and 'name' (LLM sometimes uses 'name')
    actual_pattern = pattern or name
    if not actual_pattern:
        return ToolResult(ok=False, output="", error="No search pattern provided")
    try:
        root = Path(path)
        results = []

        if target == "content":
            for p in root.rglob("*"):
                if p.is_file():
                    try:
                        content = p.read_text(encoding="utf-8", errors="ignore")
                        if actual_pattern in content:
                            results.append(str(p))
                    except Exception:
                        pass
        else:
            for p in root.rglob(actual_pattern):
                if p.is_file() or p.is_dir():
                    results.append(str(p))

        if results:
            return ToolResult(ok=True, output="\n".join(results[:50]))
        return ToolResult(ok=True, output="No matching files found.")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))
