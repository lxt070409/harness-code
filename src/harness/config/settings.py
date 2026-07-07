"""Application settings and constants."""

from pathlib import Path

# Paths
DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Guardrail audit log
GUARDRAIL_LOG = str(DATA_DIR / "guardrail_audit.jsonl")

# Memory storage
MEMORY_FILE = DATA_DIR / "memory.json"
