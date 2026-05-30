"""
NodeWalker - Lightweight Browser Control Tool for AI Agents

Control a real Chrome browser via Chrome DevTools Protocol (CDP).
Designed for AI agent integration with OpenAI-compatible tool schemas.

Usage:
    # Direct Python import
    from nodewalker import BrowserController

    async with BrowserController() as browser:
        await browser.navigate("https://example.com")
        text = await browser.get_text()
        screenshot = await browser.screenshot()

    # Or run as HTTP server
    # python -m nodewalker --port 8585
"""

from nodewalker.core.cdp_client import CDPClient
from nodewalker.core.actions import BrowserController
from nodewalker.tools.schemas import get_tool_schemas, TOOL_SCHEMAS
from nodewalker.tools.executor import ToolExecutor

__version__ = "0.1.0"
__all__ = [
    "CDPClient",
    "BrowserController",
    "ToolExecutor",
    "get_tool_schemas",
    "TOOL_SCHEMAS",
]
