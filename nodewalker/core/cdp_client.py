"""
CDP Client - Low-level Chrome DevTools Protocol interface.

Connects to a real Chrome browser via WebSocket and sends CDP commands.
Chrome must be launched with: --remote-debugging-port=9222
"""

import json
import asyncio
import aiohttp
import websockets


class CDPClient:
    """Low-level Chrome DevTools Protocol client.
    
    Connects to a running Chrome instance via its debugging port
    and provides methods to send CDP commands and receive events.
    
    Usage:
        async with CDPClient() as client:
            result = await client.send("Page.navigate", {"url": "https://example.com"})
    """

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.host = host
        self.port = port
        self._ws = None
        self._msg_id = 0
        self._responses: dict[int, asyncio.Future] = {}
        self._event_handlers: dict[str, list] = {}
        self._recv_task = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def connected(self) -> bool:
        return self._ws is not None and not self._ws.close_code

    # ── Connection ──────────────────────────────────────────────

    async def connect(self, tab_index: int = 0) -> None:
        """Connect to a Chrome tab by index (default: first tab)."""
        tabs = await self.get_tabs()
        if not tabs:
            raise ConnectionError("No Chrome tabs found. Is Chrome running with --remote-debugging-port?")
        
        if tab_index >= len(tabs):
            raise IndexError(f"Tab index {tab_index} out of range (found {len(tabs)} tabs)")

        ws_url = tabs[tab_index]["webSocketDebuggerUrl"]
        self._ws = await websockets.connect(ws_url, max_size=50 * 1024 * 1024)  # 50MB for screenshots
        self._recv_task = asyncio.create_task(self._recv_loop())

    async def disconnect(self) -> None:
        """Close the WebSocket connection."""
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
            self._recv_task = None
        if self._ws:
            await self._ws.close()
            self._ws = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()

    # ── Tab Discovery ───────────────────────────────────────────

    async def get_tabs(self) -> list[dict]:
        """Get all open tabs from Chrome."""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/json") as resp:
                tabs = await resp.json()
                # Filter to only page-type targets
                return [t for t in tabs if t.get("type") == "page"]

    async def connect_to_tab(self, tab_id: str) -> None:
        """Disconnect from current tab and connect to a specific tab by ID."""
        await self.disconnect()
        tabs = await self.get_tabs()
        for tab in tabs:
            if tab["id"] == tab_id:
                self._ws = await websockets.connect(
                    tab["webSocketDebuggerUrl"],
                    max_size=50 * 1024 * 1024,
                )
                self._recv_task = asyncio.create_task(self._recv_loop())
                return
        raise ValueError(f"Tab with id '{tab_id}' not found")

    # ── CDP Commands ────────────────────────────────────────────

    async def send(self, method: str, params: dict | None = None, timeout: float = 30) -> dict:
        """Send a CDP command and wait for the response.
        
        Args:
            method:  CDP method, e.g. "Page.navigate"
            params:  Optional parameters dict
            timeout: Seconds to wait for response (default 30)
            
        Returns:
            The 'result' dict from the CDP response
            
        Raises:
            ConnectionError: If not connected
            TimeoutError:    If response not received within timeout
            RuntimeError:    If CDP returns an error
        """
        if not self.connected:
            raise ConnectionError("Not connected to Chrome. Call connect() first.")

        self._msg_id += 1
        msg_id = self._msg_id
        
        message = {"id": msg_id, "method": method}
        if params:
            message["params"] = params

        future = asyncio.get_running_loop().create_future()
        self._responses[msg_id] = future

        await self._ws.send(json.dumps(message))

        try:
            response = await asyncio.wait_for(future, timeout)
        except asyncio.TimeoutError:
            self._responses.pop(msg_id, None)
            raise TimeoutError(f"CDP command '{method}' timed out after {timeout}s")

        if "error" in response:
            raise RuntimeError(f"CDP error: {response['error']}")

        return response.get("result", {})

    async def enable_domain(self, domain: str) -> dict:
        """Enable a CDP domain (e.g. 'Page', 'DOM', 'Network')."""
        return await self.send(f"{domain}.enable")

    # ── Event Handling ──────────────────────────────────────────

    def on(self, event: str, handler) -> None:
        """Register an event handler for a CDP event.
        
        Args:
            event:   CDP event name, e.g. "Page.loadEventFired"
            handler: Async or sync callable
        """
        if event not in self._event_handlers:
            self._event_handlers[event] = []
        self._event_handlers[event].append(handler)

    async def wait_for_event(self, event: str, timeout: float = 30) -> dict:
        """Wait for a specific CDP event to fire.
        
        Args:
            event:   CDP event name
            timeout: Seconds to wait
            
        Returns:
            Event params dict
        """
        future = asyncio.get_running_loop().create_future()

        def handler(params):
            if not future.done():
                future.set_result(params)

        self.on(event, handler)
        try:
            result = await asyncio.wait_for(future, timeout)
        finally:
            # Clean up the one-shot handler
            if event in self._event_handlers:
                self._event_handlers[event].remove(handler)
        return result

    # ── Internal ────────────────────────────────────────────────

    async def _recv_loop(self) -> None:
        """Background task: receive messages from Chrome and dispatch."""
        try:
            async for raw in self._ws:
                msg = json.loads(raw)
                
                # Response to a command
                if "id" in msg:
                    future = self._responses.pop(msg["id"], None)
                    if future and not future.done():
                        future.set_result(msg)
                
                # Event
                elif "method" in msg:
                    event = msg["method"]
                    params = msg.get("params", {})
                    for handler in self._event_handlers.get(event, []):
                        try:
                            result = handler(params)
                            if asyncio.iscoroutine(result):
                                await result
                        except Exception:
                            pass  # Don't crash recv loop on handler errors
        except websockets.ConnectionClosed:
            pass
        except asyncio.CancelledError:
            raise
