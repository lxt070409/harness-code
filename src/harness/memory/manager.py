import json
from pathlib import Path


class MemoryManager:

    def __init__(self, storage_path: str | None = None):
        from harness.config.settings import MEMORY_FILE
        self.path = Path(storage_path) if storage_path else MEMORY_FILE
        self._data: dict[str, str] = {}
        self._load()

    def _load(self):
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, Exception):
                self._data = {}

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def save(self, key: str, value: str):
        self._data[key] = value
        self._save()

    def load(self, key: str) -> str | None:
        return self._data.get(key)

    def list_keys(self) -> list[str]:
        return list(self._data.keys())

    def delete(self, key: str):
        self._data.pop(key, None)
        self._save()
