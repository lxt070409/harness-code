from harness.core.action import Action


SAMPLE_ACTIONS = [
    Action(name="file_read", params={"path": "/tmp/test.txt"}, rationale="read test file"),
    Action(name="file_write", params={"path": "/tmp/output.txt", "content": "test"}, rationale="write test output"),
    Action(name="shell_exec", params={"command": "ls -la"}, rationale="list directory contents"),
    Action(name="done", params={}, rationale="task complete"),
]
