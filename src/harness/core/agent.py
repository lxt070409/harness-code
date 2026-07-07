"""Agent — the main agent loop orchestrating LLM, guardrails, tools, and memory."""

from harness.core.action import Action
from harness.core.parser import ActionParser
from harness.core.context import ContextBuilder
from harness.core.result import ToolResult
from harness.guardrail import Verdict
from harness.guardrail.hitl import HITLPipeline
from harness.guardrail.engine import GuardrailEngine
from harness.tools.registry import ToolRegistry
from harness.memory.manager import MemoryManager


class Agent:
    """Main agent loop — orchestrates LLM, guardrails, tools, and memory."""

    def __init__(
        self,
        llm,
        guardrail: GuardrailEngine,
        tool_registry: ToolRegistry,
        memory: MemoryManager | None = None,
        max_cycles: int = 50,
    ):
        self.llm = llm
        self.guardrail = guardrail
        self.tools = tool_registry
        self.memory = memory or MemoryManager()
        self.max_cycles = max_cycles
        self.history: list[tuple[str, str]] = []

    def run(self, user_input: str) -> str:
        """Execute the full agent loop."""
        cycle = 0
        final_output = []

        while cycle < self.max_cycles:
            cycle += 1

            # 1. Build context
            memory_context = self.memory.load("project_context") or ""
            context = ContextBuilder.build(
                user_input=user_input,
                history=self.history,
                tool_registry=self.tools,
                memory_context=memory_context,
            )

            # 2. Call LLM
            response = self.llm.chat(context)
            action = ActionParser.parse(response)

            # 3. Check for done / respond / error signals
            if action.name == "done":
                final_output.append(f"[Cycle {cycle}] Task complete: {action.rationale}")
                break

            if action.name == "respond":
                # Pure conversation — no guardrail, no tool
                final_output.append(action.rationale)
                self.history.append(("assistant", action.rationale))
                break  # Single response, wait for next user input

            if action.name == "error":
                final_output.append(f"[Cycle {cycle}] Error: {action.rationale}")
                break

            # 4. Guardrail check
            verdict = self.guardrail.evaluate(action)

            if verdict == Verdict.BLOCK_ALWAYS:
                final_output.append(f"[Cycle {cycle}] ⛔ Blocked (always): {action.describe()}")
                self.history.append(("system", f"Action BLOCKED: {action.describe()}"))
                # Log the block
                self._log_guardrail(action, "block_always", "denied")
                continue

            if verdict == Verdict.BLOCK:
                msg = f"[Cycle {cycle}] ⚠️ Dangerous action detected: {action.describe()}"
                print(msg)
                approved = HITLPipeline.prompt(action)
                self._log_guardrail(action, "block", "approved" if approved else "denied")

                if not approved:
                    feedback = f"User denied: {action.describe()}"
                    final_output.append(feedback)
                    self.history.append(("system", feedback))
                    continue

            # 5. Execute tool
            result = self.tools.dispatch(action)

            # 6. Record in history with visual icon
            icon = {
                "image_read": "🖼️",
                "shell_exec": "💻",
                "file_read": "📖",
                "file_write": "✍️",
                "file_delete": "🗑️",
                "file_search": "🔍",
            }.get(action.name, "🔧")
            result_summary = f"{icon} [{action.name}] {'✅ OK' if result.ok else '❌ FAIL'}: {result.output}"
            if result.error:
                result_summary += f" | error: {result.error}"
            self.history.append(("assistant", action.describe()))
            self.history.append(("system", result_summary))
            final_output.append(result_summary)

            # 7. Check if done signal from tool
            if result.signal == "done":
                break

        if cycle >= self.max_cycles:
            final_output.append(f"[Final] Reached max cycles ({self.max_cycles}). Stopping.")

        return "\n".join(final_output)

    def run_stream(self, user_input: str):
        """Generator that yields progress events as the agent works."""
        cycle = 0
        yield {"type": "thinking", "data": "🤔 正在分析你的请求..."}

        while cycle < self.max_cycles:
            cycle += 1

            # 1. Build context
            memory_context = self.memory.load("project_context") or ""
            context = ContextBuilder.build(
                user_input=user_input,
                history=self.history,
                tool_registry=self.tools,
                memory_context=memory_context,
            )

            yield {"type": "thinking", "data": f"🤔 正在思考...（第 {cycle} 步）"}

            # 2. Call LLM
            response = self.llm.chat(context)
            action = ActionParser.parse(response)

            # 3. Check signals
            if action.name == "done":
                yield {"type": "info", "data": f"✅ {action.rationale}"}
                break

            if action.name == "respond":
                yield {"type": "result", "data": action.rationale}
                self.history.append(("assistant", action.rationale))
                break

            if action.name == "error":
                yield {"type": "error", "data": action.rationale}
                break

            # 4. Guardrail
            verdict = self.guardrail.evaluate(action)
            icon = {"image_read": "🖼️", "shell_exec": "💻", "file_read": "📖",
                    "file_write": "✍️", "file_delete": "🗑️", "file_search": "🔍"}.get(action.name, "🔧")

            if verdict == Verdict.BLOCK_ALWAYS:
                yield {"type": "blocked", "data": f"⛔ {icon} [{action.name}] 操作被禁止: {action.describe()}"}
                self.history.append(("system", f"Action BLOCKED: {action.describe()}"))
                self._log_guardrail(action, "block_always", "denied")
                continue

            if verdict == Verdict.BLOCK:
                yield {"type": "blocked", "data": f"⚠️ {icon} [{action.name}] 危险操作，需要确认: {action.describe()}"}
                # In web mode, auto-deny since there's no CLI interaction
                self._log_guardrail(action, "block", "denied")
                feedback = f"⛔ 操作被拒绝（WEB模式自动拒绝）: {action.describe()}"
                self.history.append(("system", feedback))
                yield {"type": "info", "data": feedback}
                continue

            # 5. Execute tool
            yield {"type": "tool", "data": f"{icon} 正在{ {'image_read':'识别图片','shell_exec':'执行命令','file_read':'读取文件','file_write':'写入文件','file_delete':'删除文件','file_search':'搜索文件'}.get(action.name, '执行'+action.name) }..."}
            result = self.tools.dispatch(action)

            # 6. Report result
            result_text = f"{icon} [{action.name}] {'✅ OK' if result.ok else '❌ FAIL'}"
            if result.error:
                result_text += f" | {result.error[:300]}"
            yield {"type": "tool_result", "data": result_text}

            self.history.append(("assistant", action.describe()))
            self.history.append(("system", result_text))

            if result.signal == "done":
                break

        if cycle >= self.max_cycles:
            yield {"type": "info", "data": f"⏹️ 达到最大循环次数 ({self.max_cycles})"}

    def _log_guardrail(self, action: Action, verdict: str, user_decision: str):
        """Write guardrail event to audit log."""
        import json
        from datetime import datetime
        from harness.config.settings import GUARDRAIL_LOG

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action_name": action.name,
            "params": action.params,
            "rationale": action.rationale,
            "verdict": verdict,
            "user_decision": user_decision,
        }
        try:
            with open(GUARDRAIL_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass  # Non-critical — don't crash the agent
