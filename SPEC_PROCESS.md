# SPEC Process — Brainstorming & Design Evolution

> **⚠️ STUB DOCUMENT**
> This file is a placeholder. The content below are section prompts that the user should fill in with their personal design process notes.

---

## 1. Initial Brainstorming

*TODO: Describe the initial brainstorming session. What problem were you trying to solve? What alternatives did you consider?*

- Problem space: Secure coding agent harness
- Existing solutions considered (LangChain, AutoGen, CrewAI, plain LLM)
- Why a guardrail-centric approach was chosen

---

## 2. Domain Analysis — §A.5 Requirements

*TODO: Document your analysis of the coding agent domain per §A.5 requirements:*

### 2.1 Feedback Signals

*TODO: What feedback signals exist in the coding agent domain?*

- Tool execution results (→ ToolResult)
- HITL user decisions (→ approved/denied)
- Guardrail verdicts (→ ALLOW/BLOCK/BLOCK_ALWAYS)
- LLM parsing failures (→ error action)

### 2.2 Dangerous Actions

*TODO: Catalog the dangerous actions identified and their handling strategy.*

### 2.3 Required Tools

*TODO: List the tools needed and why each was included.*

### 2.4 Memory Requirements

*TODO: Describe the memory needs of the coding agent.*

### 2.5 Key Dimension: Governance / Guardrails

*TODO: Explain why governance/guardrails was chosen as the deep dimension.*

---

## 3. Cold-Start Test Results

*TODO: Document the initial "cold-start" test approach — testing the guardrail engine without a real LLM.*

### 3.1 StubLLM Strategy

- Uses `StubLLM` with preset responses — no network, no real API
- Every test is deterministic and self-contained
- 44+ unit tests across 7 test files

### 3.2 Deterministic Demo

`python demo_mechanisms.py` demonstrates 3 scenarios deterministically:

1. **Guardrail blocks dangerous action**: `rm -rf /` → BLOCK
2. **Feedback loop**: Failed action → tool failure feedback → agent continues
3. **BLOCK_ALWAYS**: Write to `/etc/passwd` → direct rejection without HITL

### 3.3 Acceptance Criteria Verification

*TODO: Verify each acceptance criterion from SPEC.md:*

| Criterion | Status | Notes |
|-----------|--------|-------|
| Agent loop executes 3+ actions | ✅ | Integration test passes |
| Guardrail blocks `rm -rf /` | ✅ | Unit test |
| Guardrail allows `ls -la` | ✅ | Unit test |
| File op safety (`/etc` block, `/tmp` allow) | ✅ | Unit tests |
| `block_always` for `/etc/passwd` | ✅ | Unit test + Demo 3 |
| Pip unknown package block | ✅ | Unit test |
| HITL y/n/default/retry | ✅ | 4 unit tests |
| 6 tools registered | ✅ | Unit test |
| ContextBuilder assembles prompt | ✅ | Unit test |
| MemoryManager persistence | ✅ | 4 unit tests |
| CLI commands (key, init) | ✅ | 10 unit tests |
| All tests pass, no network | ✅ | CI verified |
| Mechanim demo script | ✅ | `python demo_mechanisms.py` |

---

## 4. Design Decisions & Trade-offs

*TODO: Document key design decisions and why they were made:*

- Why YAML for rules (not JSON / TOML / Python code)
- Why 3 severity levels (not more, not fewer)
- Why safety-default N in HITL
- Why `keyring` is optional (`.env` fallback)
- Why DeepSeek as primary LLM (not OpenAI directly)
- Why rules loaded at startup (no hot-reload)

---

## 5. Risks & Mitigations

*TODO: Document risks encountered during implementation and how they were addressed.*

| Risk | Impact | Mitigation |
|------|--------|------------|
| LLM JSON output instability | ActionParser failures | Code-block JSON fallback parsing |
| Rule matching granularity | Over/under-blocking | Layered approach: built-in defaults + user overrides |
| `keyring` on WSL/MSYS2 | Key storage failure | Auto-detect, fallback to `.env` |
| Image reading offline | Tool failure | Clear error message, LLM adapts |

---

## 6. What Was Left Out

*TODO: Features or approaches considered but deferred:*

- AST-level rule analysis (keyword matching only for now)
- Hot-reload of rules
- GUI interface
- Async tool execution
- Plugin system for custom tools
- Multi-model routing
