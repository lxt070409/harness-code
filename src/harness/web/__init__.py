"""Web UI for Harness — FastAPI application."""

import json
import os
from pathlib import Path
from datetime import datetime
import asyncio
import concurrent.futures

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pathlib import Path

from pydantic import BaseModel

from harness.config.settings import HARNESS_DIR, ENV_FILE
from harness.core.llm import LLMRouter
from harness.core.agent import Agent
from harness.guardrail.engine import GuardrailEngine
from harness.guardrail.rules import RuleLoader
from harness.tools.registry import ToolRegistry
from harness.tools.file_ops import file_read, file_write, file_delete, file_search
from harness.tools.shell import shell_exec
from harness.tools.image_reader import image_read
from harness.memory.manager import MemoryManager

app = FastAPI(title="Harness Agent")

# ─── API Models ───

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str
    timestamp: str

class KeySetRequest(BaseModel):
    key: str

class WorkdirRequest(BaseModel):
    path: str

class UploadResponse(BaseModel):
    status: str
    filename: str
    path: str
    size: int

class StatusResponse(BaseModel):
    model: str
    provider: str
    connected: bool
    sessions: int
    guardrail_rules: int
    tools_available: list[str]

class GuardrailEntry(BaseModel):
    timestamp: str
    action_name: str
    params: dict
    rationale: str
    verdict: str
    user_decision: str

# ─── Agent Factory ───

_agent: Agent | None = None
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
_workdir: str = str(Path.cwd())


def get_agent() -> Agent:
    global _agent
    if _agent is not None:
        return _agent

    rules_path = Path(__file__).parent.parent / "guardrail" / "default_rules.yaml"
    rules = RuleLoader.load(rules_path) if rules_path.exists() else []
    guardrail = GuardrailEngine(rules=rules)
    registry = ToolRegistry()
    registry.register_tool("file_read", "Read file content", file_read)
    registry.register_tool("file_write", "Write content to file", file_write, "sensitive")
    registry.register_tool("file_delete", "Delete file or directory", file_delete, "dangerous")
    registry.register_tool("file_search", "Search files by content or name", file_search)
    registry.register_tool("shell_exec", "Execute shell command", shell_exec, "dangerous")
    registry.register_tool("image_read", "Read/describe an image file", image_read)
    memory = MemoryManager()
    llm = LLMRouter()
    _agent = Agent(llm=llm, guardrail=guardrail, tool_registry=registry, memory=memory)
    return _agent


# ─── API Routes ───

@app.get("/api/status")
async def status():
    rules_path = Path(__file__).parent.parent / "guardrail" / "default_rules.yaml"
    rules = RuleLoader.load(rules_path) if rules_path.exists() else []
    tools = ["file_read", "file_write", "file_delete", "file_search", "shell_exec", "image_read"]
    return StatusResponse(
        model="deepseek-chat",
        provider="DeepSeek",
        connected=ENV_FILE.exists(),
        sessions=1 if _agent is not None else 0,
        guardrail_rules=len(rules),
        tools_available=tools,
    )


@app.post("/api/chat")
async def chat(req: ChatRequest):
    if not ENV_FILE.exists():
        return ChatResponse(
            reply="❌ 未配置 API Key。请在仪表盘页面设置 DeepSeek API Key，或运行 `harness key set`。",
            timestamp=datetime.now().isoformat(),
        )
    agent = get_agent()
    try:
        # Switch to configured workdir before running
        old_cwd = os.getcwd()
        os.chdir(_workdir)
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(_executor, agent.run, req.message),
            timeout=120,
        )
        os.chdir(old_cwd)
        return ChatResponse(reply=result, timestamp=datetime.now().isoformat())
    except asyncio.TimeoutError:
        return ChatResponse(
            reply="⏱️ 请求超时（120s）。Agent 正在处理的请求可能太复杂，请重试或简化需求。",
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        return ChatResponse(
            reply=f"❌ 执行出错: {str(e)[:200]}",
            timestamp=datetime.now().isoformat(),
        )


@app.get("/api/guardrail-log")
async def guardrail_log():
    from harness.config.settings import DATA_DIR
    log_path = DATA_DIR / "guardrail_audit.jsonl"
    entries = []
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    return entries[-50:]  # last 50


@app.get("/api/key/status")
async def key_status():
    return {"configured": ENV_FILE.exists()}


@app.post("/api/key")
async def key_set(req: KeySetRequest):
    ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
    # Support both DeepSeek and DashScope keys
    key = req.key
    ENV_FILE.write_text(
        f'DEEPSEEK_API_KEY="{key}"\n'
        f'DASHSCOPE_API_KEY="{key}"\n',
        encoding="utf-8",
    )
    # Reload env
    os.environ["DEEPSEEK_API_KEY"] = key
    os.environ["DASHSCOPE_API_KEY"] = key
    global _agent
    _agent = None  # force re-create with new key
    return {"status": "ok"}


@app.post("/api/key/clear")
async def key_clear():
    if ENV_FILE.exists():
        ENV_FILE.unlink()
    global _agent
    _agent = None
    return {"status": "cleared"}


@app.get("/api/config")
async def config():
    rules_path = Path(__file__).parent.parent / "guardrail" / "default_rules.yaml"
    rules = RuleLoader.load(rules_path) if rules_path.exists() else []
    return {
        "max_cycles": 50,
        "rules_count": len(rules),
        "model": "deepseek-chat",
        "workdir": _workdir,
    }


@app.get("/api/config/workdir")
async def get_workdir():
    return {"workdir": _workdir}


@app.post("/api/config/workdir")
async def set_workdir(req: WorkdirRequest):
    global _workdir
    p = Path(req.path)
    if not p.exists():
        return {"status": "error", "message": "目录不存在"}
    if not p.is_dir():
        return {"status": "error", "message": "路径不是目录"}
    _workdir = str(p.resolve())
    return {"status": "ok", "workdir": _workdir}


# ─── Upload ───

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    safe_name = file.filename.replace(" ", "_").replace("..", "_")
    dest = UPLOAD_DIR / safe_name
    content = await file.read()
    dest.write_bytes(content)
    return UploadResponse(
        status="ok",
        filename=safe_name,
        path=str(dest.resolve()),
        size=len(content),
    )


# ─── Serve Static Files ───

static_dir = Path(__file__).parent / "static"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
