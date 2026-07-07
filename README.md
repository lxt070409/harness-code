# Harness

A secure coding agent harness with a guardrail engine — because an LLM that can do anything
shouldn't be allowed to do *everything* without asking.

**Core equation:** `Agent = LLM + Harness`. This project implements the harness.

## Quick Start

```bash
pip install harness-code
harness key set       # Enter your DeepSeek API key
harness run           # Start interactive session
```

## Key Features

- **Guardrail Engine** (★ main contribution): 6 rule categories, 3 severity levels (warn/block/block_always), HITL approval
- **File Ops**: read, write, delete, search
- **Shell Execution**: run commands with guardrail protection
- **Image Reading**: describe images via Qwen-VL API
- **Memory**: cross-session key-value persistence
- **Audit Logging**: all guardrail events logged to `data/guardrail_audit.jsonl`

## Architecture

```
ContextBuilder → LLM (DeepSeek) → ActionParser → GuardrailEngine → HITL → ToolRegistry → Feedback → Loop
```

| Component        | Responsibility                                                      |
|------------------|---------------------------------------------------------------------|
| ContextBuilder   | Assembles system prompt, tool descriptions, history, memory         |
| LLMRouter        | Wraps DeepSeek API (OpenAI-compatible)                              |
| ActionParser     | Parses LLM JSON responses into `Action` objects                     |
| GuardrailEngine  | Classifies actions, matches rules, returns verdict (ALLOW/BLOCK/BLOCK_ALWAYS) |
| HITLPipeline     | Human-in-the-loop: y/n prompt for blocked actions                   |
| ToolRegistry     | Dispatches named tools (file_ops, shell, image_read)                |
| MemoryManager    | Cross-session key-value store                                       |

## Security

- API keys stored via `~/.harness/.env` with file permissions restricted on Unix
- `block_always` rules for critical system paths (no HITL bypass)
- Audit log at `data/guardrail_audit.jsonl`
- `.env` is in `.gitignore`
- Safety-default: HITL defaults to "deny" on blank input, max 3 retries then deny

### Credential Threat Model

| Threat                          | Mitigation                                                   | Residual Risk                            |
|---------------------------------|--------------------------------------------------------------|------------------------------------------|
| `.env` file read by attacker    | `.gitignore`; file permissions 600 (Unix); OS keyring (WIP)  | Local access can read plaintext          |
| Shell history leak              | No `export` usage for keys                                  | None                                     |
| Process env leak                | Read once on startup, not kept in long-lived env             | Memory dump could capture                |
| Git history leak                | `.gitignore` + pre-commit review                             | User discipline required                 |

## Distribution

- **PyPI**: `pip install harness-code`
- **Docker**: `docker build -t harness . && docker run -it harness`
- **Binary**: `pip install pyinstaller && pyinstaller src/harness/main.py`

## Known Limitations

- CLI only (no GUI)
- Default DeepSeek integration (OpenAI-compatible via config)
- Image reading requires Qwen-VL API availability (`QWEN_VL_API_KEY` or `DASHSCOPE_API_KEY`)
- Windows keyring support varies (`.env` fallback always works)
- Rules are loaded at startup — no hot-reload

## Project Structure

```
src/harness/
├── cli/              # CLI entry point, key management, init
│   ├── key_cmds.py
│   └── init_cmds.py
├── core/             # Agent loop, context, parser, LLM router, result types
│   ├── action.py     # Action dataclass
│   ├── agent.py      # Main agent loop
│   ├── context.py    # ContextBuilder
│   ├── llm.py        # LLMRouter (DeepSeek)
│   ├── parser.py     # ActionParser
│   └── result.py     # ToolResult dataclass
├── guardrail/        # GuardrailEngine, rules, classifier, HITL
│   ├── engine.py     # GuardrailEngine
│   ├── rules.py      # RuleLoader (YAML)
│   ├── classifiers.py# ActionClassifier, RuleMatcher
│   ├── hitl.py       # HITLPipeline
│   └── default_rules.yaml
├── tools/            # ToolRegistry, file_ops, shell, image_reader
│   ├── registry.py
│   ├── file_ops.py
│   ├── shell.py
│   └── image_reader.py
├── memory/           # MemoryManager
│   └── manager.py
├── config/           # Settings, defaults
│   ├── settings.py
│   └── defaults.yaml
└── main.py           # CLI entry point
tests/
├── fixture/          # StubLLM, sample_rules.yaml, sample actions
│   ├── stub_llm.py
│   ├── sample_rules.yaml
│   └── sample_action.py
├── test_guardrail_engine.py
├── test_hitl_pipeline.py
├── test_tool_registry.py
├── test_context_builder.py
├── test_memory_manager.py
├── test_agent_loop.py
└── test_cli.py
```

## Tests

```bash
pytest tests/ -v              # All tests, no network required
python demo_mechanisms.py     # 3 deterministic demonstrations
```

All tests use `StubLLM` — no real API key required, no network calls. CI runs on every push via GitHub Actions.

## License

MIT — see LICENSE for details.
