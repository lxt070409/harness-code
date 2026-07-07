# SPEC · Harness — 通用软件工程编码智能体

> 项目：AI4SE 期末项目 · A · Coding Agent Harness
> 技术栈：Python 3.11+
> 主贡献：治理 / 护栏（Guardrail Engine）

---

## 1. 问题陈述

### 1.1 要解决什么问题？

大语言模型在软件工程场景中表现出惊人的"思考"能力，但它自身缺乏执行代码、读写文件、操作系统的途径，也没有"什么时候该停下来"的判断力。现有的 agent 框架（LangChain、AutoGen、CrewAI 等）提供了高层编排能力，但将核心的治理逻辑（什么操作是安全的、出错了如何修正）封装在了框架内部，用户无法精细控制。

本项目要解决的问题是：**如何将一个只会"决定下一步做什么"的 LLM，封装为一台能稳定、安全、可治理地完成软件工程任务的系统？**

### 1.2 目标用户

- **软件工程师**：需要一个能安全读写代码仓库、执行命令、运行测试的 AI 辅助编程 agent
- **AI4SE 课程学生**：需要理解"工程师在 AI 协作中的价值落在哪一层"

### 1.3 为什么值得做？

在 AI 能完成大部分编码工作的今天，真正的工程价值落在让 AI 稳定、安全地工作的基础设施层——这是 harness 工程要回答的问题。

---

## 2. 用户故事

1. 作为一名软件工程师，我希望 agent 能读取项目中的文件，以便我无需手动打开每个文件即可了解代码结构。
2. 作为一名软件工程师，我希望 agent 能写入和修改代码文件，以便它协助我实现功能。
3. 作为一名软件工程师，我希望 agent 能执行 shell 命令（运行测试、构建项目），以便它完成编码工作流中的自动化步骤。
4. 作为一名软件工程师，我希望 agent 能搜索文件（按内容或文件名），以便快速定位相关代码。
5. 作为一名软件工程师，我希望 agent 能读取图片（截图、错误弹窗、UI 原型），以便它能辅助我排查视觉相关的 bug。
6. 作为一名关心安全的开发者，我希望危险操作（删除文件、危险 shell 命令、强制 git 推送）在执行前被拦截并请求我确认，以防误操作造成损失。
7. 作为一名多项目并行开发的工程师，我希望 agent 在当前目录下工作，不越界到系统关键路径。
8. 作为一名注重安全审计的用户，我希望所有拦截记录可追溯，以便事后检查 agent 的完整行为轨迹。

---

## 3. 功能规约

### 3.1 主循环（Agent Loop）

| 项 | 说明 |
|------|------|
| **输入** | 用户自然语言指令 |
| **行为** | 组织上下文 → 调用 LLM → 解析 JSON action → 护栏检查 → 分发执行 → 回灌结果 → 停机判断 |
| **输出** | 执行结果 / 中间状态反馈 |
| **边界** | 达到最大循环轮次（默认 50）或 LLM 返回 `done` 信号时停机 |
| **错误处理** | LLM 返回非 JSON 格式：重试 1 次并提示格式要求；仍失败则退出本轮 |

### 3.2 护栏引擎（★ 主贡献）

| 项 | 说明 |
|------|------|
| **输入** | `Action(name, params, rationale)` 对象 |
| **行为** | ActionClassifier 按 action 名路由到规则类别 → RuleMatcher 逐条匹配 → 产出 `ALLOW` / `BLOCK` / `BLOCK_ALWAYS` |
| **输出** | 判定结果 + 匹配的规则 ID |
| **规则类别** | 文件操作、Shell 执行、网络请求、Git 操作、包管理、系统边界——共 6 类 |
| **路由规则** | 所有 `shell_exec` action 统一进入 Shell 类别，再由 RuleMatcher 对 `params.command` 做命令关键词匹配（如含 `git push` 的走 Git 规则、含 `pip install` 的走包管理规则、含 `rm -rf` 的走危险命令规则） |
| **严重度分级** | `warn`（记录日志 + 打印告警，不拦截）/ `block`（拦截 + HITL）/ `block_always`（直接拒绝，不进入 HITL） |
| **边界条件** | 未匹配任何规则 → `ALLOW`；规则文件不存在 → 使用内置默认规则 |
| **错误处理** | 规则文件格式错误 → 回退到默认规则 + 告警日志 |

### 3.3 HITL 管道

| 项 | 说明 |
|------|------|
| **输入** | 护栏判定结果为 `BLOCK` 的 Action |
| **行为** | 展示操作详情（action + params + rationale）→ 等待用户输入 y/n |
| **输出** | `APPROVED` / `DENIED` |
| **边界** | 默认 N（安全优先）；空白输入视为 N；连续 3 次无效输入视为 N |
| **错误处理** | 输入异常 → 记录日志，按 DENIED 处理 |

### 3.4 ToolRegistry（工具注册与分发）

| 项 | 说明 |
|------|------|
| **输入** | `Action(name, params)` |
| **行为** | 在注册表中查找工具 → 调用对应函数 → 返回统一结果格式 |
| **输出** | `ToolResult(ok, output, error, signal)` |
| **预置工具** | `file_read`, `file_write`, `file_delete`, `file_search`, `shell_exec`, `image_read` |
| **边界条件** | 工具名未注册 → 返回错误结果；参数缺失 → 使用工具声明的默认值 |
| **错误处理** | 工具执行抛出异常 → 捕获并返回 `ToolResult(ok=False, error=...)` |

### 3.5 ContextBuilder

| 项 | 说明 |
|------|------|
| **输入** | 用户输入、对话历史、工具描述、记忆 |
| **行为** | 按固定顺序组装 system prompt + 工具描述 + 项目上下文 + 历史 + 记忆 + 本轮输入 |
| **输出** | 发送给 LLM 的完整 prompt |
| **边界** | 历史超过 20 轮时，对早期轮次做 token 级截断 |

### 3.6 MemoryManager

| 项 | 说明 |
|------|------|
| **输入** | key-value 对 |
| **行为** | 保存/读取/列出/删除持久化记忆 |
| **输出** | 读取时返回 value 或 None |
| **存储后端** | `~/.harness/memory.json` |
| **边界条件** | key 不存在时返回 None；文件损坏时重建空存储 |

---

## 4. 非功能性需求

### 4.1 性能
- 工具执行时间应小于 5 秒（网络调用如 LLM/识图除外）
- 护栏判定时间应小于 10ms
- 主循环单次迭代（不含 LLM 调用）应小于 50ms

### 4.2 安全（含凭据威胁模型）

参见 §8 凭据与分发设计。

### 4.3 可用性
- CLI 模式，单条命令启动
- 首次运行引导式配置（无配置也能启动并提示用户配置）
- 错误信息清晰可理解，不在终端爆原始 traceback

### 4.4 可观测性
- 审计日志：每次护栏拦截写入 `~/.harness/guardrail.log`（JSON Lines）
- 调试模式：`--verbose` 输出每轮 action 详情
- 运行日志：`~/.harness/harness.log`

---

## 5. 系统架构

### 5.1 组件图

```
┌─────────────────────────────────────────────────────────────┐
│                    Harness Kernel                            │
│                                                              │
│  ┌───────────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │ ContextBuilder │───▶│ LLMRouter│───▶│  ActionParser    │  │
│  └───────┬───────┘    └──────────┘    └────────┬─────────┘  │
│          │                                      │            │
│          │         ┌──────────────────────┐      │            │
│          │         │   GuardrailEngine    │◀─────┘            │
│          │         │  (★ 主要贡献)        │                   │
│          │         └──────────┬───────────┘                   │
│          │                    ▼                               │
│          │         ┌──────────────────┐                       │
│          │         │  HITLPipeline    │                       │
│          │         └────────┬─────────┘                       │
│          │                  ▼                                 │
│          │         ┌──────────────────┐                       │
│          │         │  ToolRegistry    │                       │
│          │         │  ┌──────────────┐│                       │
│          │         │  │ file_read    ││                       │
│          │         │  │ file_write   ││                       │
│          │         │  │ file_delete  ││                       │
│          │         │  │ file_search  ││                       │
│          │         │  │ shell_exec   ││                       │
│          │         │  │ image_read   ││                       │
│          │         │  └──────────────┘│                       │
│          │         └──────────────────┘                       │
│          │                  ▼                                 │
│          │         ┌──────────────────┐                       │
│          │         │  MemoryManager   │                       │
│          └─────────│  (基础实现)       │                       │
│                    └──────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 数据流

```
User Input → ContextBuilder → LLM (DeepSeek) → ActionParser → GuardrailEngine
                                                                     ↓
                                                            ┌── ALLOW ──→ ToolRegistry → ToolResult → 回灌 → 循环
                                                            └── BLOCK ──→ HITL → y → ToolRegistry
                                                                              → n → 反馈拒绝 → 循环
                                                            BLOCK_ALWAYS → 直接拒绝 + 日志 → 循环
```

### 5.3 外部依赖

| 依赖 | 用途 | 替代方案 |
|------|------|----------|
| DeepSeek API | 主模型调用 | OpenAI 兼容接口均可（可配置 base_url） |
| Qwen-VL API | 识图工具 | 其他多模态 API（可配置） |
| httpx / requests | HTTP 客户端 | — |
| keyring (可选) | OS 钥匙串存储 API Key | 纯 `.env` 兜底 |
| pytest | 测试框架 | — |

---

## 6. 数据模型

### 6.1 Action

```python
@dataclass
class Action:
    name: str           # "file_read" | "shell_exec" | ...
    params: dict        # {"path": "..."} | {"command": "..."}
    rationale: str      # LLM 提供的执行理由
```

### 6.2 ToolResult

```python
@dataclass
class ToolResult:
    ok: bool
    output: str
    error: str | None
    signal: str         # "continue" | "done" | "error"
```

### 6.3 GuardrailVerdict

```python
class Verdict(Enum):
    ALLOW = "allow"
    BLOCK = "block"          # 拦截 + HITL
    BLOCK_ALWAYS = "block_always"  # 直接拒绝
```

### 6.4 GuardrailRule（配置模型）

```python
@dataclass
class Rule:
    id: str
    category: str           # "file_operation" | "shell" | ...
    severity: str           # "block" | "block_always" | "warn"
    description: str
    match: dict             # 匹配条件（格式因 category 而异）
```

### 6.5 Tool

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: list
    func: Callable
    danger_level: str       # "safe" | "sensitive" | "dangerous"
```

---

## 7. 领域与机制设计（§A.5 额外要求）

### 7.1 该领域（coding）的反馈信号

| 信号来源 | 如何获取 | 是否代码实现 |
|----------|----------|------------|
| 工具执行结果 | ToolRegistry 返回的 ToolResult | ✅ |
| HITL 用户决策 | HITLPipeline 返回 A/B | ✅ |
| 护栏判定结果 | GuardrailEngine 返回 Verdict | ✅ |
| LLM 解析失败 | ActionParser 检测到非 JSON | ✅ |

### 7.2 危险动作

| 动作类别 | 危险等级 | 处理方式 |
|----------|----------|----------|
| `rm -rf /` 等高危 shell | DANGEROUS | Guardrail BLOCK → HITL |
| 删除项目根目录 | DANGEROUS | Guardrail BLOCK → HITL |
| Git force push | DANGEROUS | Guardrail BLOCK → HITL |
| 写 /etc/ 等系统路径 | CRITICAL | Guardrail BLOCK_ALWAYS |
| 安装未知 PyPI 包 | SENSITIVE | Guardrail BLOCK → HITL |
| 外发数据到未知目标 | DANGEROUS | Guardrail BLOCK → HITL |

### 7.3 所需工具

文件读写、文件搜索、shell 执行、图片识别——共 6 个预置工具。

### 7.4 记忆需求

基础 key-value 持久化，不做深。跨会话记住项目结构和用户偏好。

### 7.5 重点维度：治理 / 护栏

选择此维度深入实现的理由：

1. **天然由代码构成**：规则分类、模式匹配、严重度分级、HITL 状态机——全是确定性逻辑，不需要 LLM 参与。
2. **最符合 §A.4(C) 的判据**：移除了真实 LLM 后，护栏引擎仍然能用 20+ 个确定性单元测试完整验证其行为。
3. **对软件工程安全有真实价值**：相比"在提示词里写一句注意安全"，一个可配置、可审计、可测试的护栏是生产级 agent 的必需品。
4. **扩展性好**：可以从关键词匹配一路做到 AST 分析、权限矩阵，在"深度"方向有足够的挖掘空间。

---

## 8. 凭据与分发设计

### 8.1 API Key 存储方案

**三层策略：**

1. **首选**：`keyring` 库 → 操作系统的 Credential Manager / Keychain / Secret Service
2. **次选**：`~/.harness/.env` 文件 → `python-dotenv` 加载
3. **兜底**：首次运行 `getpass` 隐藏输入引导

**威胁模型：**

| 威胁 | 缓解 | 残余风险 |
|------|------|----------|
| `.env` 文件被读取 | `.gitignore` 排除；文件权限 `600`；优先使用 OS 钥匙串 | 本地访问权限可直接读文件 |
| Shell history 泄露 | 不用 `export` 形式设置 key | 无此风险 |
| 进程环境泄露 | 仅启动时读取，不保存在长时环境变量 | 内存 dump 可读取 |
| Git 历史泄露 | `.gitignore` + 提交前自查 | 仍需用户自律 |

**Key 管理命令：**

```
harness key set       隐藏输入设置
harness key status    显示是否已配置（不输出明文）
harness key clear     删除已存储的 key
harness key update    覆盖旧 key
```

### 8.2 分发方案

**选型：PyPI 包分发**

```
pip install harness-code
harness init      # 引导录入 key
harness run       # 启动交互式 agent
```

**已知限制：**
- 仅 CLI 模式，无 GUI 界面
- 默认仅 DeepSeek 原生支持（OpenAI 兼容接口可手动配置）
- 识图功能依赖 Qwen-VL API 可用性
- Windows 下 `keyring` 可能需要额外配置（兜底 `.env` 可用）

---

## 9. 技术选型与理由

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.11+ | LLM 生态最成熟；开发节奏快；已有环境 |
| LLM 供应商 | DeepSeek | 低成本、响应快、OpenAI 兼容接口 |
| 识图 | Qwen-VL API（现有 skill 封装） | 已有可用接口，无需自建 |
| 测试框架 | pytest | 事实标准 |
| 配置格式 | YAML | 可读性好，适合规则配置 |
| HTTP 客户端 | httpx | 异步支持（为后续扩展预留） |
| 钥匙串接口 | keyring（可选） | 标准化接口，跨平台 |
| 分发 | PyPI (build + twine) | Python 项目最自然的选择 |

---

## 10. 验收标准

| 功能 | 验收标准 |
|------|----------|
| 主循环 | 可在一次对话中连续执行 3+ 个 action 并返回最终结果 |
| 护栏 - 危险 shell | `rm -rf /` 返回 BLOCK，`ls -la` 返回 ALLOW |
| 护栏 - 文件操作 | 删除 `/etc` 返回 BLOCK，删除 `/tmp` 返回 ALLOW |
| 护栏 - block_always | 写 `/etc/passwd` 返回 BLOCK_ALWAYS（不触发 HITL） |
| 护栏 - 包管理 | `pip install unknown-pkg` 返回 BLOCK，`pip install requests` 返回 ALLOW |
| 护栏 - Git force push | `git push --force` 返回 BLOCK |
| HITL | 用户输入 y 放行，n/空/无效 拒绝 |
| ToolRegistry | 6 个工具均可注册、查找、分发 |
| ContextBuilder | system prompt + 工具描述 + 历史 + 记忆 正确组装 |
| MemoryManager | set/get/delete 工作，重启后数据保留 |
| 凭据 | 首次运行引导录入，key set/status/clear 命令完整 |
| 测试 | `pytest tests/` 全部通过，不依赖网络和真实 LLM |
| 机制演示 | `python demo_mechanisms.py` 在 mock LLM 下展示 3 个确定性场景 |

---

## 11. 风险与未决问题

| 风险 | 影响 | 缓解 |
|------|------|------|
| DeepSeek API 在 JSON 格式输出上不够稳定 | ActionParser 解析失败率升高 | 设置 system prompt 强调 JSON 格式；Parser 实现部分容错（模糊匹配） |
| 规则配置的匹配粒度 | 颗粒度过粗会漏放危险行为，过细则维护成本高 | 采用分层策略：内置默认规则 + 用户可覆盖扩展 |
| `keyring` 在 WSL/MSYS2 环境下不可用 | 首选举措部分失效 | 自动检测环境，fallback 到 `.env` |
| 识图依赖外部 API | 离线不可用 | 工具执行失败时返回清晰错误；LLM 会收到失败反馈并调整策略 |

**未决问题：**
- 规则引擎是否需要支持正则表达式 vs 仅 glob/前缀匹配？（按正则设计，用户可配置）
- 是否需要支持运行时热加载规则文件？（暂不支持，启动时加载一次）
- 是否需要对 LLM 的 action 返回值做 schema 校验？（基础实现，不深度校验）
