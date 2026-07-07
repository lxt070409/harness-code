"""Tests for CLI entry point, KeyManager, and init command."""

from harness.cli.key_cmds import KeyManager
from harness.cli import init_cmds
from harness.cli.init_cmds import init


def test_key_set_and_status(monkeypatch, tmp_path):
    """Test key set and status flow using temp storage."""
    key_file = tmp_path / ".env"
    # Patch the ENV_FILE reference inside key_cmds module (where it's imported)
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    import getpass
    monkeypatch.setattr(getpass, "getpass", lambda *a: "sk-test-key-12345")

    km = KeyManager()
    km.set_key()
    assert km.has_key() is True


def test_key_clear(monkeypatch, tmp_path):
    """Test clearing a previously stored key."""
    key_file = tmp_path / ".env"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text('DEEPSEEK_API_KEY="sk-test"')
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    km = KeyManager()
    km.clear_key()
    assert key_file.exists() is False
    assert km.has_key() is False


def test_key_status_no_key(monkeypatch, tmp_path):
    """Status reports no key when none configured."""
    key_file = tmp_path / ".env"
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    km = KeyManager()
    assert km.has_key() is False


def test_key_update(monkeypatch, tmp_path):
    """Update replaces existing key."""
    key_file = tmp_path / ".env"
    key_file.parent.mkdir(parents=True, exist_ok=True)
    key_file.write_text('DEEPSEEK_API_KEY="sk-old"')
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    import getpass
    monkeypatch.setattr(getpass, "getpass", lambda *a: "sk-new-key")

    km = KeyManager()
    km.update_key()

    content = key_file.read_text()
    assert "sk-new-key" in content
    assert "DEEPSEEK_API_KEY" in content


def test_key_set_empty_cancels(monkeypatch, tmp_path, capsys):
    """Setting an empty key prints cancel message, does not write file."""
    key_file = tmp_path / ".env"
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    import getpass
    monkeypatch.setattr(getpass, "getpass", lambda *a: "")

    km = KeyManager()
    km.set_key()

    captured = capsys.readouterr()
    assert "Cancelled" in captured.out
    assert key_file.exists() is False


def test_init_creates_directory(monkeypatch, tmp_path):
    """Init creates ~/.harness directory and memory.json."""
    harness_dir = tmp_path / ".harness"
    # Patch the HARNESS_DIR reference inside init_cmds module
    monkeypatch.setattr("harness.cli.init_cmds.HARNESS_DIR", harness_dir)

    init()

    assert harness_dir.exists()
    memory_file = harness_dir / "memory.json"
    assert memory_file.exists()
    assert memory_file.read_text() == "{}"


def test_init_already_exists(monkeypatch, tmp_path, capsys):
    """Init when already configured prints message and doesn't recreate."""
    harness_dir = tmp_path / ".harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("harness.cli.init_cmds.HARNESS_DIR", harness_dir)

    init()

    captured = capsys.readouterr()
    assert "already configured" in captured.out


def test_init_with_force(monkeypatch, tmp_path):
    """Init with --force re-initializes even when already configured."""
    harness_dir = tmp_path / ".harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("harness.cli.init_cmds.HARNESS_DIR", harness_dir)

    init(force=True)

    assert harness_dir.exists()
    memory_file = harness_dir / "memory.json"
    assert memory_file.exists()


def test_cli_key_set_subcommand(monkeypatch, tmp_path):
    """CLI dispatches 'key set' subcommand correctly."""
    key_file = tmp_path / ".env"
    monkeypatch.setattr("harness.cli.key_cmds.ENV_FILE", key_file)

    import getpass
    monkeypatch.setattr(getpass, "getpass", lambda *a: "sk-cli-test")

    from harness.main import cli
    monkeypatch.setattr("sys.argv", ["harness", "key", "set"])
    cli()

    assert key_file.exists()
    assert "sk-cli-test" in key_file.read_text()


def test_cli_init_subcommand(monkeypatch, tmp_path):
    """CLI dispatches 'init' subcommand correctly."""
    harness_dir = tmp_path / ".harness"
    monkeypatch.setattr("harness.cli.init_cmds.HARNESS_DIR", harness_dir)

    from harness.main import cli
    monkeypatch.setattr("sys.argv", ["harness", "init"])
    cli()

    assert harness_dir.exists()
    assert (harness_dir / "memory.json").exists()


def test_default_rules_yaml_exists():
    """Verify default_rules.yaml is present and valid."""
    from pathlib import Path
    import yaml

    rules_path = (
        Path(__file__).resolve().parent.parent
        / "src"
        / "harness"
        / "guardrail"
        / "default_rules.yaml"
    )
    assert rules_path.exists(), f"default_rules.yaml not found at {rules_path}"

    with open(rules_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data is not None
    assert "rules" in data
    assert len(data["rules"]) > 0

    # Verify each rule has required fields
    for rule in data["rules"]:
        assert "id" in rule
        assert "category" in rule
        assert "severity" in rule
        assert "description" in rule
        assert "match" in rule
