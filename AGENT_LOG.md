# Agent Log

Chronological log of all implementation tasks with commit hashes and skills used.

## Task 0: Specification & Planning
- **Skills**: brainstorming, writing-plans
- **Commit**: `49bfc85` — SPEC: harness design with guardrail engine as main contribution
- **Commit**: `fd33fe0` — PLAN: 9-task implementation plan for coding agent harness
- **Notes**: Full SPEC.md defining architecture, data models, user stories, acceptance criteria, credential threat model, and 9-task PLAN.md.

## Task 1: Project Scaffolding & Data Models
- **Skills**: brainstorming, writing-plans
- **Commit**: `ff67797` — feat: project scaffolding, data models, test fixtures
- **Notes**: Foundation data types (`Action`, `ToolResult`, `Rule`, `Verdict`, `Tool`), test fixtures (`StubLLM`, `sample_rules.yaml`), `pyproject.toml`, `.gitignore`.

## Task 2: Guardrail Engine — Core
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `6baa41c` — feat: guardrail engine core - RuleLoader, ActionClassifier, GuardrailEngine
- **Notes**: `GuardrailEngine` with `RuleLoader` (YAML), `ActionClassifier` (action-name → category routing), `RuleMatcher` (glob + regex matching). 3 severity levels: warn/block/block_always. 7 unit tests covering shell/file/git/pip rules.

## Task 3: HITL Pipeline
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `4b4665d` — feat: HITL pipeline with y/n prompt, retry, safety-default
- **Notes**: `HITLPipeline.prompt()` with y/n input, safety-default N, max 3 retries. Blocked actions presented with action name, params, rationale. 4 unit tests covering approve/deny/default/retry.

## Task 4: ToolRegistry and Base Tools
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `80a8f50` — feat: ToolRegistry and base tools — file_ops, shell, image_reader
- **Notes**: `ToolRegistry` (register/dispatch/describe), 6 tools: `file_read`, `file_write`, `file_delete`, `file_search`, `shell_exec`, `image_read`. Each tool returns `ToolResult(ok, output, error, signal)`. 8 unit tests.

## Task 5: ContextBuilder and MemoryManager
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `7aed68a` — feat: ContextBuilder and MemoryManager
- **Notes**: `ContextBuilder.build()` assembles system prompt + tool descriptions + history (last 20) + memory + user input. `MemoryManager` with JSON-backed key-value persistence. 4 unit tests.

## Task 6: LLM Router and Agent Loop
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `5a2fc71` — feat: LLM Router, ActionParser, Agent main loop
- **Notes**: `LLMRouter` wraps DeepSeek API with httpx. `ActionParser` parses JSON (supports markdown code block extraction). `Agent.run()` orchestrates the full cycle: context → LLM → parse → guardrail → HITL → dispatch → feedback → loop. Done/error/max-cycles termination signals. Audit logging. 3 integration tests.

## Task 7: CLI and Key Management
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: `0af7f46` — feat: CLI, key management, default rules, init command
- **Notes**: `harness run|key set|key status|key clear|key update|init` commands. `KeyManager` stores API key in `~/.harness/.env`. `init` creates `~/.harness/` with `memory.json`. `default_rules.yaml` with 7 pre-configured rules. 10 unit tests.

## Task 8: Mechanism Demo Script
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: Part of Task 9
- **Notes**: `demo_mechanisms.py` — 3 deterministic demonstrations using `StubLLM` (no real network):
  1. Guardrail blocks `rm -rf /` → BLOCK
  2. Feedback loop: failed action → tool failure → agent continues with next action
  3. BLOCK_ALWAYS: write to `/etc/passwd` → direct rejection without HITL

## Task 9: CI, README, Project Documents
- **Skills**: writing-plans, subagent-driven-development
- **Commit**: (this commit)
- **Notes**: CI config (`.github/workflows/test.yml`), `README.md`, `AGENT_LOG.md`, `SPEC_PROCESS.md` (stub), `REFLECTION.md` (stub). Full test suite passes (44+ tests).
