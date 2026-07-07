"""Conversation storage — persists chat conversations to disk."""

import json
import uuid
from pathlib import Path
from datetime import datetime


class ConversationStore:
    """Stores conversations as JSON files under ~/.harness/conversations/."""

    def __init__(self, storage_dir: str | None = None):
        self.dir = Path(storage_dir) if storage_dir else Path.home() / ".harness" / "conversations"
        self.dir.mkdir(parents=True, exist_ok=True)

    def _path(self, conv_id: str) -> Path:
        return self.dir / f"{conv_id}.json"

    def list(self) -> list[dict]:
        """Return all conversations sorted by last activity (newest first)."""
        convs = []
        for f in sorted(self.dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    convs.append({
                        "id": data["id"],
                        "title": data.get("title", "新对话"),
                        "created_at": data.get("created_at", ""),
                        "updated_at": data.get("updated_at", ""),
                        "message_count": len(data.get("messages", [])),
                    })
                except (json.JSONDecodeError, KeyError):
                    pass
        return convs

    def create(self, title: str = "新对话") -> dict:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now().isoformat()
        data = {"id": conv_id, "title": title, "created_at": now, "updated_at": now, "messages": []}
        self._path(conv_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def get(self, conv_id: str) -> dict | None:
        p = self._path(conv_id)
        if not p.exists():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def add_message(self, conv_id: str, role: str, content: str) -> dict | None:
        data = self.get(conv_id)
        if not data:
            return None
        now = datetime.now().isoformat()
        data["messages"].append({"role": role, "content": content, "timestamp": now})
        data["updated_at"] = now
        # Auto-title from first user message
        if data["title"] == "新对话" and role == "user":
            data["title"] = content[:30] + ("…" if len(content) > 30 else "")
        self._path(conv_id).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def delete(self, conv_id: str) -> bool:
        p = self._path(conv_id)
        if p.exists():
            p.unlink()
            return True
        return False

    def get_or_create_current(self) -> dict:
        """Get the most recent conversation or create one."""
        convs = self.list()
        if convs:
            data = self.get(convs[0]["id"])
            if data:
                return data
        return self.create()
