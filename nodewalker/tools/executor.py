"""
Tool Executor - Dispatches AI tool calls to browser actions.

Receives a tool name + arguments from any AI agent,
executes the corresponding browser action, and returns the result.
"""

from nodewalker.core.actions import BrowserController


class ToolExecutor:
    """Executes browser tools called by AI agents.
    
    Usage:
        executor = ToolExecutor(browser_controller)
        result = await executor.execute("navigate", {"url": "https://example.com"})
    """

    def __init__(self, browser: BrowserController):
        self.browser = browser
        self._action_map = {
            "navigate": self._navigate,
            "click": self._click,
            "type_text": self._type_text,
            "press_key": self._press_key,
            "screenshot": self._screenshot,
            "get_text": self._get_text,
            "get_html": self._get_html,
            "evaluate": self._evaluate,
            "scroll": self._scroll,
            "wait_for": self._wait_for,
            "get_tabs": self._get_tabs,
            "switch_tab": self._switch_tab,
            "get_console_logs": self._get_console_logs,
            "clear_console_logs": self._clear_console_logs,
            "get_network_logs": self._get_network_logs,
            "clear_network_logs": self._clear_network_logs,
            "get_page_snapshot": self._get_page_snapshot,
            "click_ref": self._click_ref,
            "type_ref": self._type_ref,
            "find_elements": self._find_elements,
            "hover": self._hover,
            "select_option": self._select_option,
            "go_back": self._go_back,
            "go_forward": self._go_forward,
            "handle_dialog": self._handle_dialog,
            "get_cookies": self._get_cookies,
            "set_cookie": self._set_cookie,
            "check_element": self._check_element,
            "extract_data": self._extract_data,
            "get_page_errors": self._get_page_errors,
            "wait_for_navigation": self._wait_for_navigation,
            "fill_form": self._fill_form,
            "drag_drop": self._drag_drop,
        }

    @property
    def tool_count(self) -> int:
        return len(self._action_map)

    async def execute(self, tool_name: str, arguments: dict) -> dict:
        """Execute a tool by name with given arguments.
        
        Args:
            tool_name: Name of the tool (e.g. "navigate", "click").
            arguments: Tool arguments as a dict.
            
        Returns:
            Result dict from the tool action.
        """
        action = self._action_map.get(tool_name)
        if not action:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            return await action(arguments)
        except Exception as e:
            return {"success": False, "error": f"Tool '{tool_name}' failed: {str(e)}"}

    # ── Action Dispatchers ──────────────────────────────────────

    async def _navigate(self, args: dict) -> dict:
        return await self.browser.navigate(
            url=args["url"],
            wait_for_load=args.get("wait_for_load", True),
        )

    async def _click(self, args: dict) -> dict:
        return await self.browser.click(selector=args["selector"])

    async def _type_text(self, args: dict) -> dict:
        return await self.browser.type_text(
            selector=args["selector"],
            text=args["text"],
            clear_first=args.get("clear_first", True),
        )

    async def _press_key(self, args: dict) -> dict:
        return await self.browser.press_key(key=args["key"])

    async def _screenshot(self, args: dict) -> dict:
        return await self.browser.screenshot(
            format=args.get("format", "png"),
            quality=args.get("quality", 80),
        )

    async def _get_text(self, args: dict) -> dict:
        return await self.browser.get_text(
            selector=args.get("selector"),
            max_length=args.get("max_length", 0),
        )

    async def _get_html(self, args: dict) -> dict:
        return await self.browser.get_html(
            selector=args.get("selector"),
        )

    async def _evaluate(self, args: dict) -> dict:
        return await self.browser.evaluate(
            expression=args["expression"],
        )

    async def _scroll(self, args: dict) -> dict:
        return await self.browser.scroll(
            direction=args.get("direction", "down"),
            amount=args.get("amount", 500),
        )

    async def _wait_for(self, args: dict) -> dict:
        return await self.browser.wait_for(
            selector=args["selector"],
            timeout=args.get("timeout", 10),
        )

    async def _get_tabs(self, args: dict) -> dict:
        return await self.browser.get_tabs()

    async def _switch_tab(self, args: dict) -> dict:
        return await self.browser.switch_tab(tab_id=args["tab_id"])

    # ── Console & Network Dispatchers ───────────────────────────

    async def _get_console_logs(self, args: dict) -> dict:
        return await self.browser.get_console_logs(
            level=args.get("level"),
            clear=args.get("clear", False),
        )

    async def _clear_console_logs(self, args: dict) -> dict:
        return await self.browser.clear_console_logs()

    async def _get_network_logs(self, args: dict) -> dict:
        return await self.browser.get_network_logs(
            url_filter=args.get("url_filter"),
            method_filter=args.get("method_filter"),
            clear=args.get("clear", False),
        )

    async def _clear_network_logs(self, args: dict) -> dict:
        return await self.browser.clear_network_logs()

    # ── Snapshot & Ref Dispatchers ──────────────────────────────

    async def _get_page_snapshot(self, args: dict) -> dict:
        return await self.browser.get_page_snapshot(
            max_depth=args.get("max_depth", 15),
            compact=args.get("compact", False),
        )

    async def _click_ref(self, args: dict) -> dict:
        return await self.browser.click_ref(ref=args["ref"])

    async def _type_ref(self, args: dict) -> dict:
        return await self.browser.type_ref(
            ref=args["ref"],
            text=args["text"],
            clear_first=args.get("clear_first", True),
            press_enter=args.get("press_enter", False),
        )

    # ── New Feature Dispatchers ─────────────────────────────────

    async def _find_elements(self, args: dict) -> dict:
        return await self.browser.find_elements(
            query=args["query"],
            role=args.get("role"),
            max_results=args.get("max_results", 20),
        )

    async def _hover(self, args: dict) -> dict:
        return await self.browser.hover(ref=args["ref"])

    async def _select_option(self, args: dict) -> dict:
        return await self.browser.select_option(
            ref=args["ref"],
            value=args.get("value", ""),
            label=args.get("label", ""),
        )

    async def _go_back(self, args: dict) -> dict:
        return await self.browser.go_back()

    async def _go_forward(self, args: dict) -> dict:
        return await self.browser.go_forward()

    async def _handle_dialog(self, args: dict) -> dict:
        return await self.browser.handle_dialog(
            accept=args.get("accept", True),
            text=args.get("text", ""),
        )

    async def _get_cookies(self, args: dict) -> dict:
        return await self.browser.get_cookies(url=args.get("url", ""))

    async def _set_cookie(self, args: dict) -> dict:
        return await self.browser.set_cookie(
            name=args["name"], value=args["value"], domain=args["domain"],
            path=args.get("path", "/"),
            http_only=args.get("http_only", False),
            secure=args.get("secure", False),
        )

    async def _check_element(self, args: dict) -> dict:
        return await self.browser.check_element(ref=args["ref"])

    async def _extract_data(self, args: dict) -> dict:
        return await self.browser.extract_data(
            instruction=args["instruction"],
            selector=args.get("selector", "body"),
        )

    async def _get_page_errors(self, args: dict) -> dict:
        return await self.browser.get_page_errors()

    async def _wait_for_navigation(self, args: dict) -> dict:
        return await self.browser.wait_for_navigation(
            timeout=args.get("timeout", 10),
        )

    async def _fill_form(self, args: dict) -> dict:
        return await self.browser.fill_form(
            fields=args["fields"],
        )

    async def _drag_drop(self, args: dict) -> dict:
        return await self.browser.drag_drop(
            from_ref=args["from_ref"],
            to_ref=args["to_ref"],
        )
