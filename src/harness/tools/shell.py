import subprocess
from harness.core.result import ToolResult


def shell_exec(command: str, timeout: int = 30, cwd: str | None = None) -> ToolResult:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return ToolResult(
            ok=result.returncode == 0,
            output=output[:10000],
            error=result.stderr if result.returncode != 0 else None,
        )
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, output="", error=f"Command timed out after {timeout}s")
    except Exception as e:
        return ToolResult(ok=False, output="", error=str(e))