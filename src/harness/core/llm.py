"""LLM Router — wraps DeepSeek API calls."""

import json
import os
import httpx
from dotenv import load_dotenv


class LLMRouter:
    """Wraps DeepSeek API calls. Can be replaced by StubLLM for testing."""

    def __init__(self, model: str = "deepseek-chat", temperature: float = 0.3, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        load_dotenv()
        self.api_key = os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.base_url = base_url.rstrip("/")

    def chat(self, prompt: str) -> dict:
        if not self.api_key:
            return {"action": "error", "params": {}, "rationale": "No API key configured. Run 'harness key set' first."}

        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                },
                timeout=60,
            )
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                # Try to parse as JSON
                from harness.core.parser import ActionParser

                parsed = ActionParser.parse_json(content)
                if parsed:
                    return parsed
                return {
                    "action": "error",
                    "params": {"raw": content},
                    "rationale": "LLM returned non-JSON response",
                }
            else:
                return {
                    "action": "error",
                    "params": {},
                    "rationale": f"API error: {response.status_code}",
                }
        except Exception as e:
            return {"action": "error", "params": {}, "rationale": f"LLM call failed: {str(e)}"}
