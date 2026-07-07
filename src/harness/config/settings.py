import os
from pathlib import Path

HARNESS_DIR = Path.home() / ".harness"
HARNESS_DIR.mkdir(parents=True, exist_ok=True)

ENV_FILE = HARNESS_DIR / ".env"
MEMORY_FILE = HARNESS_DIR / "memory.json"
GUARDRAIL_LOG = HARNESS_DIR / "guardrail.log"
RUN_LOG = HARNESS_DIR / "harness.log"
