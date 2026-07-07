from harness.tools.registry import ToolRegistry


class ContextBuilder:

    SYSTEM_PROMPT = """You are a coding assistant with access to a set of tools.
You help the user by deciding which tool to call and returning structured actions.

You MUST respond in the following JSON format ONLY:

- To use a tool:
  {"action": "<tool_name>", "params": {...}, "rationale": "<why this action>"}

- To answer a question or chat (no tool needed):
  {"action": "respond", "params": {}, "rationale": "<your reply here>"}

- When the task is complete:
  {"action": "done", "params": {}, "rationale": "task complete"}

Available tools will be listed below. Use them when the user asks you to read,
write, search files, execute commands, or analyze images. Use "respond" for
normal conversation, questions, greetings, or any situation that doesn't need
a tool.
"""

    @classmethod
    def build(cls, user_input: str, history: list, tool_registry: ToolRegistry | None = None,
              memory_context: str = "") -> str:
        parts = [cls.SYSTEM_PROMPT]

        if tool_registry:
            parts.append("\n---\n" + tool_registry.describe_tools())

        if memory_context:
            parts.append("\n---\n[Memory]\n" + memory_context)

        if history:
            parts.append("\n---\n[Conversation History]")
            for role, content in history[-20:]:  # keep last 20
                parts.append(f"[{role}]: {content[:500]}")

        parts.append("\n---\n[User]\n" + user_input)
        parts.append("\n---\nRespond with JSON action:")

        return "\n".join(parts)
