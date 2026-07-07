"""Init command — initializes harness configuration directory."""

from harness.config.settings import HARNESS_DIR


def init(force: bool = False):
    """Initialize harness configuration directory.

    Creates ~/.harness/ with memory.json if not already present.
    Use --force to re-initialize.
    """
    if HARNESS_DIR.exists() and not force:
        print(f"✅ Harness already configured at {HARNESS_DIR}")
        print("   Run with --force to re-initialize.")
        return

    HARNESS_DIR.mkdir(parents=True, exist_ok=True)

    # Create default memory file
    memory_file = HARNESS_DIR / "memory.json"
    if not memory_file.exists():
        memory_file.write_text("{}", encoding="utf-8")

    print(f"✅ Harness initialized at {HARNESS_DIR}")
    print("   Next step: run 'harness key set' to configure your API key.")
