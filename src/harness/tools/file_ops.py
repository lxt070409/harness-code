from pathlib import Path
from harness.core.result import ToolResult


def file_read(path: str, offset: int = 0, limit: int = -1) -> ToolResult:
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(ok=False, output="", error=f"File not found: {path}")
        content = p.read_text(encoding="utf-8", errors="replace")
        if offset > 0:
            lines = content.splitlines(keepends=True)
            content = "".join(lines[offset:])
        if limit > 0:
            content = content[:limit]
        return ToolResult(ok=True, output=content)
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_write(path: str, content: str) -> ToolResult:
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return ToolResult(ok=True, output=f"Wrote {len(content)} bytes to {path}")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_delete(path: str, recursive: bool = False) -> ToolResult:
    try:
        p = Path(path)
        if not p.exists():
            return ToolResult(ok=False, output="", error=f"Path not found: {path}")
        if p.is_dir():
            if recursive:
                import shutil
                shutil.rmtree(p)
            else:
                p.rmdir()
        else:
            p.unlink()
        return ToolResult(ok=True, output=f"Deleted: {path}")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))


def file_search(pattern: str, target: str = "content", path: str = ".", file_glob: str = "") -> ToolResult:
    try:
        search_path = Path(path)
        if target == "files":
            matches = list(search_path.rglob(pattern))
            if matches:
                output = "\n".join(str(m.relative_to(search_path)) for m in matches[:50])
            else:
                output = "No files found"
        elif target == "content":
            import subprocess
            cmd = ["grep", "-r", "-n", pattern, str(search_path)]
            if file_glob:
                cmd.extend(["--include", file_glob])
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            output = result.stdout[:5000] if result.stdout else "No matches found" if result.returncode == 1 else result.stderr
        else:
            return ToolResult(ok=False, output="", error=f"Unknown search target: {target}")

        return ToolResult(ok=True, output=output)
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))