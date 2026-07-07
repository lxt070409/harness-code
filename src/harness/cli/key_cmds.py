"""Key manager — stores and manages API keys in .env file."""

import os
import getpass
from harness.config.settings import ENV_FILE


class KeyManager:
    """Manage DeepSeek API key storage in .env file."""

    def __init__(self):
        self.env_file = ENV_FILE

    def set_key(self):
        """Prompt user for API key and save it securely."""
        print("Enter your DeepSeek API Key (input will be hidden):")
        key = getpass.getpass()
        if not key.strip():
            print("No key entered. Cancelled.")
            return

        # Verify key (simple format check)
        if not key.startswith("sk-"):
            print("Warning: Key doesn't start with 'sk-'. This may not be a valid key.")

        self._write_env(key)
        print("API Key saved to", self.env_file)
        print("⚠️  Note: .env is plaintext. For production, use OS keyring (coming soon).")

    def status(self):
        """Check if a key is configured."""
        if self.has_key():
            print("✅ API Key is configured.")
            key_value = self._read_env().get("DEEPSEEK_API_KEY", "Not set")
            prefix = key_value[:6] if len(key_value) > 6 else key_value
            print(f"   Provider: {prefix}...")
        else:
            print("❌ No API Key configured.")
            print("   Run 'harness key set' to configure.")

    def clear_key(self):
        """Remove the stored API key."""
        if self.env_file.exists():
            self.env_file.unlink()
            print("API Key cleared.")
        else:
            print("No key configured.")

    def update_key(self):
        """Replace existing key."""
        self.clear_key()
        self.set_key()

    def has_key(self) -> bool:
        """Check if a key is stored."""
        return self.env_file.exists() and "DEEPSEEK_API_KEY" in self.env_file.read_text()

    def _write_env(self, key: str):
        """Write key to .env file."""
        self.env_file.parent.mkdir(parents=True, exist_ok=True)
        content = f'DEEPSEEK_API_KEY="{key}"\n'
        content += f'DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"\n'
        self.env_file.write_text(content, encoding="utf-8")
        # Set restrictive permissions (Unix)
        if os.name != "nt":
            self.env_file.chmod(0o600)

    def _read_env(self) -> dict:
        """Read .env file into a dictionary."""
        result = {}
        if self.env_file.exists():
            for line in self.env_file.read_text().splitlines():
                if "=" in line:
                    k, v = line.split("=", 1)
                    result[k.strip()] = v.strip().strip('"')
        return result
