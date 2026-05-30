# 🚀 NodeWalker

[![PyPI version](https://badge.fury.io/py/nodewalker.svg)](https://badge.fury.io/py/nodewalker)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Nhqvu2005/NodeWalker/workflows/Tests/badge.svg)](https://github.com/Nhqvu2005/NodeWalker/actions)

**Lightweight Browser Control Tool for AI Agents**

Control a real Chrome browser via Chrome DevTools Protocol (CDP). Designed so that **any AI agent** can read the tool definitions and start controlling the browser immediately.

## Quick Start

### 1. Install

**From PyPI (recommended):**
```bash
pip install nodewalker
```

**From source:**
```bash
git clone https://github.com/Nhqvu2005/NodeWalker.git
cd NodeWalker
pip install -e .
```

**With Docker:**
```bash
docker-compose up -d
```
See [DOCKER.md](DOCKER.md) for detailed Docker instructions.

### 2. Start Chrome with Remote Debugging
```bash
# Windows
start chrome --remote-debugging-port=9222

# macOS
open -a "Google Chrome" --args --remote-debugging-port=9222

# Linux
google-chrome --remote-debugging-port=9222
```

### 3. Start NodeWalker Server
```bash
python -m nodewalker
# Server starts at http://127.0.0.1:8585
```

### 4. Use It

**From any HTTP client (curl, AI agent, etc):**
```bash
# Discover available tools
curl http://localhost:8585/tools

# Navigate to a page
curl -X POST http://localhost:8585/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "navigate", "arguments": {"url": "https://example.com"}}'

# Take a screenshot
curl -X POST http://localhost:8585/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "screenshot", "arguments": {}}'
```

**From Python (direct import):**
```python
from nodewalker import BrowserController

async with BrowserController() as browser:
    await browser.navigate("https://example.com")
    text = await browser.get_text()
    await browser.click("#submit")
    shot = await browser.screenshot()
```

## Integration with AI Agents

### OpenAI
```python
import requests, openai

# Load tool schemas from NodeWalker
tools = requests.get("http://localhost:8585/tools").json()

response = openai.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Go to google.com and search for NodeWalker"}],
    tools=tools
)

# Execute the tool call
tool_call = response.choices[0].message.tool_calls[0]
result = requests.post("http://localhost:8585/execute", json={
    "tool": tool_call.function.name,
    "arguments": json.loads(tool_call.function.arguments)
}).json()
```

### Any Other AI
Just read `TOOLS.md` for the complete tool reference, or call `GET /tools` for the JSON schema.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/tools` | GET | Tool schemas (OpenAI format) |
| `/tools/summary` | GET | Plain text tool summary |
| `/execute` | POST | Execute a tool |
| `/health` | GET | Health check |
| `/reconnect` | POST | Reconnect to Chrome |

## CLI Options

```
python -m nodewalker [OPTIONS]

  --port         HTTP server port (default: 8585)
  --chrome-port  Chrome debugging port (default: 9222)
  --host         Bind address (default: 127.0.0.1)
```

## Features

- 🎯 **27 Browser Tools** – navigate, click, type, screenshot, evaluate, scroll, and more
- 🤖 **AI-Ready** – OpenAI-compatible schemas, works with GPT-4, Claude, and any LLM
- 🚀 **Zero Setup** – connects to your existing Chrome, no browser spawning
- 🐳 **Docker Support** – containerized deployment with Chrome included
- 📦 **Lightweight** – only 4 core dependencies
- 🔌 **Extensible** – easy to add custom tools
- 📚 **Well Documented** – complete examples and API reference

## Architecture

```
Any AI Agent ──HTTP──► NodeWalker (FastAPI) ──CDP/WebSocket──► Real Chrome
```

- **Zero browser spawning** – connects to your existing Chrome
- **27 tools** – navigate, click, type, screenshot, evaluate, scroll, console logs, network logs, etc.
- **4 dependencies** – websockets, aiohttp, fastapi, uvicorn
- **AI-agnostic** – standard JSON schema, works with any LLM

## Examples

Check out the [examples/](examples/) directory for complete working examples:

- **Basic Navigation** – Navigate, screenshot, extract text
- **Form Filling** – Automate login forms
- **Web Scraping** – Multi-page data extraction
- **OpenAI Integration** – Let GPT-4 control the browser
- **Claude Integration** – Let Claude control the browser

```python
# See examples/01_basic_navigation.py for full code
async with BrowserController() as browser:
    await browser.navigate("https://example.com")
    text = await browser.get_text()
    screenshot = await browser.screenshot()
```
