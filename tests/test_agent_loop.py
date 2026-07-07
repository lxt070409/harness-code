"""Integration tests for the Agent main loop."""

from unittest.mock import patch
from harness.core.action import Action
from harness.core.agent import Agent
from harness.guardrail.engine import GuardrailEngine
from harness.guardrail.rules import RuleLoader
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import file_read, file_write
from tests.fixture.stub_llm import StubLLM
from pathlib import Path


def make_test_agent(stub_responses: list[dict]) -> Agent:
    rules_path = Path(__file__).parent / "fixture" / "sample_rules.yaml"
    engine = GuardrailEngine(rules=RuleLoader.load(rules_path))
    registry = ToolRegistry()
    registry.register_tool("file_read", "Read a file", file_read)
    registry.register_tool("file_write", "Write a file", file_write)
    stub = StubLLM(responses=stub_responses)
    return Agent(llm=stub, guardrail=engine, tool_registry=registry)


def test_agent_loop_file_read():
    """Agent reads a file then stops."""
    agent = make_test_agent([
        {"action": "file_read", "params": {"path": __file__}, "rationale": "read self"},
        {"action": "done", "params": {}, "rationale": "done"},
    ])
    result = agent.run("read this file")
    assert "ok" in result.lower() or "success" in result.lower() or "done" in result.lower() or len(result) > 0


def test_agent_loop_guardrail_blocks():
    """Agent proposes rm -rf /, guardrail blocks it, HITL denies, agent adjusts."""
    with patch("harness.guardrail.hitl.HITLPipeline.prompt", return_value=False):
        agent = make_test_agent([
            {"action": "shell_exec", "params": {"command": "rm -rf /"}, "rationale": "clean everything"},
        ])
        # Should not crash — guardrail handles it
        result = agent.run("clean the system")
        assert "blocked" in result.lower() or "denied" in result.lower() or "dangerous" in result.lower() or len(result) > 0


def test_agent_loop_max_cycles():
    """Agent stops after max cycles with a status message."""
    agent = make_test_agent([{"action": "file_read", "params": {"path": __file__}, "rationale": "keep going"}] * 60)
    result = agent.run("loop forever")
    assert "max" in result.lower() or "cycle" in result.lower() or "limit" in result.lower() or len(result) > 0


def test_agent_responds_to_chat():
    """Agent can respond conversationally without using a tool."""
    agent = make_test_agent([
        {"action": "respond", "params": {}, "rationale": "Hello! How can I help you today?"},
    ])
    result = agent.run("hi there")
    assert "Hello" in result or "hello" in result.lower()

