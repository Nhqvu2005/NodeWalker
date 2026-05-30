"""
NodeWalker HTTP API Server.

FastAPI server that exposes browser control tools via HTTP.
Any AI agent can call these endpoints to control the browser.

Endpoints:
    GET  /tools    → Tool schemas (OpenAI function calling format)
    POST /execute  → Execute a browser tool
    GET  /health   → Health check + connection status
"""

import asyncio
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from nodewalker.core.actions import BrowserController
from nodewalker.tools.schemas import get_tool_schemas, get_tool_summary
from nodewalker.tools.executor import ToolExecutor


# ── Globals ─────────────────────────────────────────────────────

_browser: BrowserController | None = None
_executor: ToolExecutor | None = None
_chrome_port: int = int(os.environ.get("NODEWALKER_CHROME_PORT", "9222"))


# ── Request/Response Models ────────────────────────────────────

class ToolCallRequest(BaseModel):
    tool: str
    arguments: dict = {}


class ToolCallResponse(BaseModel):
    success: bool
    result: dict = {}
    error: str | None = None


# ── App Lifecycle ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Connect to Chrome on startup, disconnect on shutdown."""
    global _browser, _executor

    # Retry connection with exponential backoff
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            _browser = BrowserController(port=_chrome_port)
            await _browser.connect()
            _executor = ToolExecutor(_browser)
            print(f"[OK] Connected to Chrome on port {_chrome_port}")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = retry_delay * (2 ** attempt)
                print(f"[RETRY] Connection failed (attempt {attempt + 1}/{max_retries}): {e}")
                print(f"        Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
            else:
                print(f"[WARN] Could not connect to Chrome after {max_retries} attempts: {e}")
                print(f"       Start Chrome with: chrome --remote-debugging-port={_chrome_port}")
                _executor = None

    yield

    if _browser:
        await _browser.disconnect()
        print("[OFF] Disconnected from Chrome")


# ── FastAPI App ────────────────────────────────────────────────

app = FastAPI(
    title="NodeWalker",
    description="Browser Control Tool for AI Agents",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Endpoints ──────────────────────────────────────────────────

@app.get("/tools")
async def get_tools():
    """Return all available tool schemas in OpenAI function calling format.
    
    AI agents should call this endpoint first to discover available tools.
    The response can be passed directly to OpenAI's `tools` parameter.
    """
    return get_tool_schemas()


@app.get("/tools/summary")
async def get_tools_text():
    """Return a plain-text summary of all tools (for system prompts)."""
    return {"summary": get_tool_summary()}


@app.post("/execute", response_model=ToolCallResponse)
async def execute_tool(request: ToolCallRequest):
    """Execute a browser control tool.
    
    Send the tool name and arguments, receive the result.
    
    Example request body:
        {"tool": "navigate", "arguments": {"url": "https://example.com"}}
    """
    if _executor is None:
        raise HTTPException(
            status_code=503,
            detail="Not connected to Chrome. Start Chrome with --remote-debugging-port"
        )
    
    result = await _executor.execute(request.tool, request.arguments)
    
    if result.get("success"):
        return ToolCallResponse(success=True, result=result)
    else:
        return ToolCallResponse(
            success=False,
            result=result,
            error=result.get("error", "Unknown error")
        )


@app.post("/reconnect")
async def reconnect(tab_index: int = 0):
    """Reconnect to Chrome (useful if Chrome was restarted)."""
    global _browser, _executor
    if _browser:
        await _browser.disconnect()
    
    _browser = BrowserController(port=_chrome_port)
    try:
        await _browser.connect(tab_index=tab_index)
        _executor = ToolExecutor(_browser)
        return {"success": True, "message": f"Reconnected to Chrome port {_chrome_port}"}
    except Exception as e:
        _executor = None
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint. Returns connection status."""
    connected = _browser is not None and _browser.cdp.connected
    return {
        "status": "ok" if connected else "disconnected",
        "connected": connected,
        "chrome_port": _chrome_port,
        "version": "0.1.0",
    }


def create_app(chrome_port: int = 9222) -> FastAPI:
    """Factory function to create the app with custom Chrome port."""
    global _chrome_port
    _chrome_port = chrome_port
    return app
