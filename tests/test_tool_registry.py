from pathlib import Path
from harness.core.action import Action
from harness.core.result import ToolResult
from harness.tools import Tool
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import file_read, file_write, file_delete, file_search
from harness.tools.shell import shell_exec


class TestToolRegistry:

    def setup_method(self):
        self.registry = ToolRegistry()
        self.registry.register(Tool(name="file_read", description="Read a file", func=file_read))
        self.registry.register(Tool(name="file_write", description="Write a file", func=file_write))
        self.registry.register(Tool(name="file_delete", description="Delete a file", func=file_delete))

    def test_dispatch_existing_tool(self):
        result = self.registry.dispatch(Action("file_read", {"path": __file__}))
        assert result.ok is True
        assert "TestToolRegistry" in result.output

    def test_dispatch_unknown_tool(self):
        result = self.registry.dispatch(Action("unknown_tool", {}))
        assert result.ok is False
        assert "not found" in result.error

    def test_describe_tools(self):
        desc = self.registry.describe_tools()
        assert "file_read" in desc
        assert "file_write" in desc

    def test_register_duplicate(self):
        registry = ToolRegistry()
        registry.register(Tool(name="dup", description="a", func=lambda: None))
        registry.register(Tool(name="dup", description="b", func=lambda: None))
        desc = registry.describe_tools()
        assert desc.count("dup") == 1


class TestFileOps:

    def test_file_read_nonexistent(self, tmp_path):
        result = file_read(path=str(tmp_path / "nope.txt"))
        assert result.ok is False
        assert "not found" in result.error.lower() or "No such file" in result.error or result.error != ""

    def test_file_write_and_read(self, tmp_path):
        target = tmp_path / "test_write.txt"
        write_result = file_write(path=str(target), content="hello world")
        assert write_result.ok is True

        read_result = file_read(path=str(target))
        assert read_result.ok is True
        assert "hello world" in read_result.output

    def test_file_delete(self, tmp_path):
        target = tmp_path / "to_delete.txt"
        target.write_text("delete me")
        assert target.exists()

        result = file_delete(path=str(target))
        assert result.ok is True
        assert not target.exists()

    def test_file_search_content(self, tmp_path):
        (tmp_path / "search_me.py").write_text("def foo():\n    pass")
        result = file_search(pattern="def foo", target="content", path=str(tmp_path))
        assert result.ok is True
        assert "search_me.py" in result.output

    def test_file_search_name(self, tmp_path):
        (tmp_path / "find_me.txt").write_text("data")
        result = file_search(pattern="find_me*", target="files", path=str(tmp_path))
        assert result.ok is True
        assert "find_me.txt" in result.output