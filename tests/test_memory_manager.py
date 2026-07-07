from harness.memory.manager import MemoryManager


def test_memory_save_and_load(tmp_path):
    mm = MemoryManager(storage_path=str(tmp_path / "test_memory.json"))
    mm.save("project", "harness")
    assert mm.load("project") == "harness"


def test_memory_load_nonexistent(tmp_path):
    mm = MemoryManager(storage_path=str(tmp_path / "test_memory.json"))
    assert mm.load("nonexistent") is None


def test_memory_list_keys(tmp_path):
    mm = MemoryManager(storage_path=str(tmp_path / "test_memory.json"))
    mm.save("a", "1")
    mm.save("b", "2")
    keys = mm.list_keys()
    assert "a" in keys
    assert "b" in keys


def test_memory_delete(tmp_path):
    mm = MemoryManager(storage_path=str(tmp_path / "test_memory.json"))
    mm.save("temp", "value")
    mm.delete("temp")
    assert mm.load("temp") is None
