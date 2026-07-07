from harness.core.context import ContextBuilder
from harness.core.action import Action


def test_context_builds_minimal():
    ctx = ContextBuilder.build(user_input="hello", history=[])
    assert "hello" in ctx
    assert "Available tools" in ctx  # default tool description


def test_context_includes_history():
    history = [
        ("user", "list files"),
        ("assistant", Action("shell_exec", {"command": "ls"}, "list").describe()),
        ("system", "output: file1.txt\nfile2.txt"),
    ]
    ctx = ContextBuilder.build(user_input="read file1", history=history)
    assert "file1.txt" in ctx
    assert "read file1" in ctx
