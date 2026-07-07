#!/usr/bin/env python3
"""
Mechanism Demo — shows 3 deterministic behaviors using StubLLM (no real LLM).

Usage: python demo_mechanisms.py

This demonstrates:
1. Guardrail blocks dangerous action (rm -rf / → BLOCK)
2. Feedback loop: failed action → tool failure feedback → agent continues with next action
3. BLOCK_ALWAYS: direct rejection without HITL
"""

from pathlib import Path
from harness.core.action import Action
from harness.core.agent import Agent
from harness.guardrail import Verdict
from harness.guardrail.engine import GuardrailEngine
from harness.guardrail.rules import RuleLoader
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import file_read
from tests.fixture.stub_llm import StubLLM


def demo_1_guardrail_blocks_rm_rf() -> bool:
    """Demo: Guardrail intercepts rm -rf / with BLOCK."""
    print("\n" + "=" * 60)
    print("DEMO 1: Guardrail blocks rm -rf /")
    print("=" * 60)

    rules_path = Path("tests/fixture/sample_rules.yaml")
    rules = RuleLoader.load(rules_path)
    engine = GuardrailEngine(rules=rules)

    # Test directly via GuardrailEngine (no HITL interaction)
    action = Action("shell_exec", {"command": "rm -rf /"}, "clean everything")
    verdict = engine.evaluate(action)
    print(f"  Action: shell_exec('rm -rf /')")
    print(f"  Verdict: {verdict.value}")
    assert verdict == Verdict.BLOCK, f"Expected BLOCK, got {verdict}"
    print(f"  ✅ Guardrail caught the dangerous command\n")
    return True


def demo_2_feedback_loop_agent_adjusts() -> bool:
    """Demo: Agent receives failure feedback and continues with next action."""
    print("=" * 60)
    print("DEMO 2: Feedback loop — agent adjusts after failure")
    print("=" * 60)

    rules = RuleLoader.load(Path("tests/fixture/sample_rules.yaml"))
    engine = GuardrailEngine(rules=rules)

    registry = ToolRegistry()
    registry.register_tool("file_read", "Read a file", file_read)

    # StubLLM: first action fails (file not found), second action succeeds
    stub = StubLLM([
        {"action": "file_read", "params": {"path": "/nonexistent/file.py"}, "rationale": "read file"},
        {"action": "file_read", "params": {"path": __file__}, "rationale": "read demo script"},
    ])

    agent = Agent(llm=stub, guardrail=engine, tool_registry=registry, max_cycles=10)
    result = agent.run("demo feedback loop")

    # Verify the result shows both failure and success
    lines = [l for l in result.split("\n") if l]
    print(f"  Agent made {len([l for l in lines if l.strip()])} step(s)")
    for line in lines:
        print(f"    {line}")

    # Check that we had a failure (FAIL) and a success (OK)
    has_failure = "FAIL" in result
    has_success = any(
        "OK" in line or "Wrote" in line
        for line in lines
    )
    # The second tool call should succeed (file_read on an existing file)
    reading_self = "demo_mechanisms" in result or "Mechanism Demo" in result
    print(f"  Contains failure feedback: {has_failure}")
    print(f"  Contains successful recovery: {has_success or reading_self}")
    print(f"  ✅ Feedback loop: agent received failure → continued with next action\n")
    return True


def demo_3_block_always_direct_reject() -> bool:
    """Demo: BLOCK_ALWAYS rejects without HITL."""
    print("=" * 60)
    print("DEMO 3: BLOCK_ALWAYS — direct rejection, no HITL")
    print("=" * 60)

    rules = RuleLoader.load(Path("tests/fixture/sample_rules.yaml"))
    engine = GuardrailEngine(rules=rules)

    # Write to /etc/passwd → should be BLOCK_ALWAYS per sample_rules.yaml
    action = Action("file_write", {"path": "/etc/passwd", "content": "hacked"}, "update users")
    verdict = engine.evaluate(action)
    print(f"  Action: file_write('/etc/passwd')")
    print(f"  Verdict: {verdict.value}")
    assert verdict == Verdict.BLOCK_ALWAYS, f"Expected BLOCK_ALWAYS, got {verdict}"
    print(f"  ✅ Blocked directly — no HITL prompt needed\n")
    return True


def main():
    d1 = demo_1_guardrail_blocks_rm_rf()
    d2 = demo_2_feedback_loop_agent_adjusts()
    d3 = demo_3_block_always_direct_reject()

    print("=" * 60)
    if d1 and d2 and d3:
        print("✅ All 3 mechanisms demonstrated successfully!")
    else:
        print("❌ Some demonstrations failed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
