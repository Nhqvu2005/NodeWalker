"""
Browser Actions - High-level browser control built on CDP client.

Provides a clean, async API for common browser interactions:
navigate, click, type, screenshot, get_text, etc.
"""

import asyncio
import base64
from nodewalker.core.cdp_client import CDPClient


class BrowserController:
    """High-level browser controller for AI agents.
    
    Wraps CDP commands into simple, intuitive actions.
    
    Usage:
        async with BrowserController() as browser:
            await browser.navigate("https://example.com")
            text = await browser.get_text()
            await browser.click("#submit-btn")
            shot = await browser.screenshot()
    """

    MAX_LOG_ENTRIES = 200

    def __init__(self, host: str = "localhost", port: int = 9222):
        self.cdp = CDPClient(host=host, port=port)
        self._page_enabled = False
        self._console_logs: list[dict] = []
        self._network_logs: list[dict] = []
        self._network_responses: dict[str, dict] = {}
        self._ref_map: dict[int, int] = {}  # ref_number -> backendDOMNodeId
        self._ref_counter = 0

    async def connect(self, tab_index: int = 0) -> None:
        """Connect to Chrome and enable required domains."""
        await self.cdp.connect(tab_index=tab_index)
        await self.cdp.enable_domain("Page")
        await self.cdp.enable_domain("Runtime")
        await self.cdp.enable_domain("DOM")
        await self.cdp.enable_domain("Network")
        await self.cdp.enable_domain("Accessibility")
        self._page_enabled = True

        # Listen for console messages
        self.cdp.on("Runtime.consoleAPICalled", self._on_console)
        # Listen for network events
        self.cdp.on("Network.requestWillBeSent", self._on_request)
        self.cdp.on("Network.responseReceived", self._on_response)

    def _on_console(self, params):
        """Handler for Runtime.consoleAPICalled events."""
        args = params.get("args", [])
        values = []
        for arg in args:
            if "value" in arg:
                values.append(str(arg["value"]))
            elif arg.get("type") == "object":
                desc = arg.get("description", arg.get("className", "[object]"))
                values.append(desc)
            else:
                values.append(arg.get("description", str(arg.get("type", ""))))
        
        entry = {
            "type": params.get("type", "log"),
            "text": " ".join(values),
            "timestamp": params.get("timestamp", 0),
        }
        self._console_logs.append(entry)
        if len(self._console_logs) > self.MAX_LOG_ENTRIES:
            self._console_logs.pop(0)

    def _on_request(self, params):
        """Handler for Network.requestWillBeSent events."""
        req = params.get("request", {})
        request_id = params.get("requestId", "")
        entry = {
            "request_id": request_id,
            "method": req.get("method", ""),
            "url": req.get("url", ""),
            "type": params.get("type", ""),
            "timestamp": params.get("timestamp", 0),
            "status": None,
            "status_text": None,
            "mime_type": None,
            "response_time": None,
        }
        self._network_logs.append(entry)
        if len(self._network_logs) > self.MAX_LOG_ENTRIES:
            self._network_logs.pop(0)

    def _on_response(self, params):
        """Handler for Network.responseReceived events."""
        resp = params.get("response", {})
        request_id = params.get("requestId", "")
        # Update matching request entry with response info
        for entry in reversed(self._network_logs):
            if entry["request_id"] == request_id:
                entry["status"] = resp.get("status")
                entry["status_text"] = resp.get("statusText", "")
                entry["mime_type"] = resp.get("mimeType", "")
                break

    # ── Accessibility Tree Snapshot ──────────────────────────────

    # Roles that are interactive (AI can act on them)
    INTERACTIVE_ROLES = {
        "button", "link", "textbox", "searchbox", "combobox",
        "checkbox", "radio", "switch", "slider", "spinbutton",
        "tab", "menuitem", "menuitemcheckbox", "menuitemradio",
        "option", "treeitem",
    }

    # Roles to skip entirely (noise)
    SKIP_ROLES = {
        "none", "presentation", "generic", "InlineTextBox",
        "LineBreak", "StaticText",
    }

    # Roles to include in compact mode (interactive + structural)
    COMPACT_ROLES = {
        # Interactive
        "button", "link", "textbox", "combobox", "checkbox", "radio",
        "switch", "slider", "spinbutton", "searchbox", "menuitem",
        "tab", "option", "menuitemcheckbox", "menuitemradio",
        # Structural
        "heading", "banner", "main", "navigation", "complementary",
        "contentinfo", "form", "dialog", "alertdialog", "alert",
        "tablist", "toolbar", "menu", "menubar",
        # Content
        "image", "table", "row", "cell", "columnheader",
        "article", "list", "listitem",
        # Root
        "RootWebArea",
    }

    async def get_page_snapshot(self, max_depth: int = 15, compact: bool = False) -> dict:
        """Get an accessibility tree snapshot of the page.
        
        Returns a structured view with [ref=N] tags on interactive elements.
        The AI agent can use these refs with click_ref() and type_ref().
        
        Args:
            max_depth: Maximum tree depth to traverse (default 15).
            compact: If True, only show interactive elements, headings,
                     landmarks, and images. Dramatically reduces tokens.
            
        Returns:
            {"success": True, "snapshot": text, "ref_count": n, "url": url, "title": title}
        """
        # Reset ref map
        self._ref_map.clear()
        self._ref_counter = 0

        # Get full accessibility tree
        result = await self.cdp.send("Accessibility.getFullAXTree")
        nodes = result.get("nodes", [])

        if not nodes:
            return {"success": False, "error": "Could not retrieve accessibility tree"}

        # Build lookup: nodeId -> AXNode
        node_map: dict[str, dict] = {}
        for node in nodes:
            node_map[node["nodeId"]] = node

        # Get page URL and title
        url_result = await self.cdp.send("Runtime.evaluate", {
            "expression": "window.location.href",
            "returnByValue": True,
        })
        title_result = await self.cdp.send("Runtime.evaluate", {
            "expression": "document.title",
            "returnByValue": True,
        })
        url = url_result.get("result", {}).get("value", "")
        title = title_result.get("result", {}).get("value", "")

        # Find root node (first node is typically root)
        root = nodes[0] if nodes else None
        if not root:
            return {"success": False, "error": "Empty accessibility tree"}

        # Build compact tree text
        lines: list[str] = []
        self._walk_ax_tree(root, node_map, lines, depth=0,
                          max_depth=max_depth, compact=compact)

        snapshot_text = "\n".join(lines)

        return {
            "success": True,
            "snapshot": snapshot_text,
            "ref_count": self._ref_counter,
            "url": url,
            "title": title,
            "compact": compact,
        }

    def _walk_ax_tree(self, node: dict, node_map: dict, lines: list[str],
                      depth: int, max_depth: int, compact: bool = False) -> None:
        """Recursively walk the AX tree and build compact text representation."""
        if depth > max_depth:
            return

        # Skip ignored nodes
        if node.get("ignored", False):
            # Still walk children of ignored nodes
            for child_id in node.get("childIds", []):
                child = node_map.get(child_id)
                if child:
                    self._walk_ax_tree(child, node_map, lines, depth, max_depth, compact)
            return

        role_obj = node.get("role", {})
        role = role_obj.get("value", "") if isinstance(role_obj, dict) else ""
        
        name_obj = node.get("name", {})
        name = name_obj.get("value", "") if isinstance(name_obj, dict) else ""
        
        value_obj = node.get("value", {})
        value = value_obj.get("value", "") if isinstance(value_obj, dict) else ""

        # Skip noise roles
        if role in self.SKIP_ROLES:
            for child_id in node.get("childIds", []):
                child = node_map.get(child_id)
                if child:
                    self._walk_ax_tree(child, node_map, lines, depth, max_depth, compact)
            return

        # Compact mode: only show important roles
        show_this_node = True
        if compact and role not in self.COMPACT_ROLES:
            show_this_node = False

        # Build the line
        is_interactive = role in self.INTERACTIVE_ROLES

        # Assign ref to interactive elements (always, even if node hidden in compact)
        ref_tag = ""
        if is_interactive:
            self._ref_counter += 1
            ref_num = self._ref_counter
            backend_id = node.get("backendDOMNodeId")
            if backend_id is not None:
                self._ref_map[ref_num] = backend_id
            ref_tag = f" [ref={ref_num}]"

        if show_this_node and (role or name):
            indent = "  " * depth

            # Compact mode: shorter name truncation
            max_name_len = 80 if compact else 120
            max_val_len = 50 if compact else 80

            # Format: role "name" [ref=N] value="..."
            line = f"{indent}{role}"
            if name:
                display_name = name[:max_name_len] + "..." if len(name) > max_name_len else name
                line += f' "{display_name}"'
            line += ref_tag
            if value:
                display_val = value[:max_val_len] + "..." if len(value) > max_val_len else value
                line += f' value="{display_val}"'

            # Add properties like checked, expanded, etc.
            props = node.get("properties", [])
            for prop in props:
                prop_name = prop.get("name", "")
                prop_val = prop.get("value", {})
                pv = prop_val.get("value") if isinstance(prop_val, dict) else prop_val
                if prop_name in ("checked", "expanded", "selected", "disabled", "required") and pv:
                    line += f" {prop_name}={pv}"

            lines.append(line)

        # Walk children
        for child_id in node.get("childIds", []):
            child = node_map.get(child_id)
            if child:
                # In compact mode, don't increase depth for hidden nodes
                next_depth = depth + 1 if show_this_node else depth
                self._walk_ax_tree(child, node_map, lines, next_depth, max_depth, compact)

    # ── Ref-Based Interactions ──────────────────────────────────

    async def click_ref(self, ref: int) -> dict:
        """Click an element by its ref number from get_page_snapshot.
        
        Args:
            ref: The ref number assigned in the snapshot (e.g. 3).
            
        Returns:
            {"success": True, "ref": ref, "clicked": {...}}
        """
        if ref not in self._ref_map:
            return {
                "success": False,
                "error": f"Ref {ref} not found. Call get_page_snapshot first to get valid refs."
            }

        backend_node_id = self._ref_map[ref]

        # Resolve backendDOMNodeId to a Runtime object for coordinate lookup
        try:
            resolve_result = await self.cdp.send("DOM.resolveNode", {
                "backendNodeId": backend_node_id,
            })
            object_id = resolve_result.get("object", {}).get("objectId")
            if not object_id:
                return {"success": False, "error": f"Could not resolve DOM node for ref {ref}"}

            # Get bounding box
            box_js = """
            function() {
                const rect = this.getBoundingClientRect();
                return {
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2,
                    tag: this.tagName?.toLowerCase() || '',
                    text: (this.innerText || this.textContent || '').substring(0, 100)
                };
            }
            """
            call_result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": box_js,
                "returnByValue": True,
            })
            value = call_result.get("result", {}).get("value")
            if not value:
                return {"success": False, "error": f"Element for ref {ref} has no bounding box (may be hidden)"}

            x, y = value["x"], value["y"]

            # Scroll into view first
            await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": "function() { this.scrollIntoViewIfNeeded(); }",
            })
            await asyncio.sleep(0.1)

            # Re-get coordinates after scroll
            call_result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": box_js,
                "returnByValue": True,
            })
            value = call_result.get("result", {}).get("value", value)
            x, y = value["x"], value["y"]

            # Dispatch click
            for event_type in ["mouseMoved", "mousePressed", "mouseReleased"]:
                await self.cdp.send("Input.dispatchMouseEvent", {
                    "type": event_type,
                    "x": x,
                    "y": y,
                    "button": "left",
                    "clickCount": 1,
                })

            return {
                "success": True,
                "ref": ref,
                "clicked": {"tag": value.get("tag", ""), "text": value.get("text", "")},
            }
        except Exception as e:
            return {"success": False, "error": f"Click ref {ref} failed: {str(e)}"}

    async def type_ref(self, ref: int, text: str, clear_first: bool = True,
                       press_enter: bool = False) -> dict:
        """Type text into an element by its ref number from get_page_snapshot.
        
        Uses native value setter + event dispatch for React/Vue/Angular
        compatibility. Falls back to key-by-key for contenteditable elements.
        
        Args:
            ref: The ref number of the input element.
            text: Text to type.
            clear_first: Whether to clear existing text first.
            press_enter: Whether to press Enter after typing.
            
        Returns:
            {"success": True, "ref": ref, "typed": text}
        """
        if ref not in self._ref_map:
            return {
                "success": False,
                "error": f"Ref {ref} not found. Call get_page_snapshot first to get valid refs."
            }

        backend_node_id = self._ref_map[ref]

        try:
            # Resolve to JS object
            resolve_result = await self.cdp.send("DOM.resolveNode", {
                "backendNodeId": backend_node_id,
            })
            object_id = resolve_result.get("object", {}).get("objectId")
            if not object_id:
                return {"success": False, "error": f"Could not resolve DOM node for ref {ref}"}

            # Framework-compatible input: use native value setter + events
            # This works with React, Vue, Angular, Svelte, and vanilla JS
            js_type = """function(text, clearFirst) {
                // Focus
                this.focus();
                
                // Check if contenteditable
                if (this.isContentEditable) {
                    if (clearFirst) this.textContent = '';
                    // For contenteditable, insert via execCommand
                    document.execCommand('insertText', false, text);
                    return {method: 'contenteditable', tag: this.tagName.toLowerCase()};
                }
                
                // For input/textarea: use native value setter for framework compatibility
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    this.tagName === 'TEXTAREA' 
                        ? window.HTMLTextAreaElement.prototype 
                        : window.HTMLInputElement.prototype, 
                    'value'
                );
                
                if (nativeSetter && nativeSetter.set) {
                    if (clearFirst) {
                        nativeSetter.set.call(this, '');
                        this.dispatchEvent(new Event('input', {bubbles: true}));
                    }
                    nativeSetter.set.call(this, text);
                } else {
                    if (clearFirst) this.value = '';
                    this.value = text;
                }
                
                // Dispatch all events that frameworks listen to
                this.dispatchEvent(new Event('input', {bubbles: true}));
                this.dispatchEvent(new Event('change', {bubbles: true}));
                this.dispatchEvent(new KeyboardEvent('keydown', {bubbles: true, key: 'a'}));
                this.dispatchEvent(new KeyboardEvent('keyup', {bubbles: true, key: 'a'}));
                
                return {method: 'native_setter', tag: this.tagName.toLowerCase(), value: this.value};
            }"""

            result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": js_type,
                "arguments": [
                    {"value": text},
                    {"value": clear_first},
                ],
                "returnByValue": True,
            })

            # Press Enter if requested
            if press_enter:
                await self.cdp.send("Input.dispatchKeyEvent", {
                    "type": "keyDown", "key": "Enter", "code": "Enter",
                    "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
                })
                await self.cdp.send("Input.dispatchKeyEvent", {
                    "type": "keyUp", "key": "Enter", "code": "Enter",
                    "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
                })

            info = result.get("result", {}).get("value", {})
            return {"success": True, "ref": ref, "typed": text, "method": info.get("method", "unknown")}
        except Exception as e:
            return {"success": False, "error": f"Type ref {ref} failed: {str(e)}"}

    async def disconnect(self) -> None:
        await self.cdp.disconnect()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *exc):
        await self.disconnect()

    # ── Navigation ──────────────────────────────────────────────

    async def navigate(self, url: str, wait_for_load: bool = True) -> dict:
        """Navigate to a URL.
        
        Auto-prepends https:// if no protocol is specified.
        
        Args:
            url: The URL to navigate to.
            wait_for_load: If True, wait for the page to fully load.
            
        Returns:
            {"success": True, "url": url, "title": page_title}
        """
        # Auto-prepend https:// if missing
        if not url.startswith(('http://', 'https://', 'file://', 'data:', 'about:')):
            url = f'https://{url}'
        
        if wait_for_load:
            load_future = self.cdp.wait_for_event("Page.loadEventFired", timeout=30)
        
        result = await self.cdp.send("Page.navigate", {"url": url})
        
        if "errorText" in result:
            return {"success": False, "error": result["errorText"]}
        
        if wait_for_load:
            await load_future

        # Get the page title after navigation
        title_result = await self.cdp.send("Runtime.evaluate", {
            "expression": "document.title"
        })
        title = title_result.get("result", {}).get("value", "")
        
        return {"success": True, "url": url, "title": title}

    # ── Click ───────────────────────────────────────────────────

    async def click(self, selector: str) -> dict:
        """Click an element by CSS selector.
        
        Auto-scrolls into view and retries coordinates. Falls back to
        JS .click() if element has zero bounding box.
        
        Args:
            selector: CSS selector of the element to click.
            
        Returns:
            {"success": True, "selector": selector}
        """
        # Scroll into view and get center coordinates
        js = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            el.scrollIntoView({{block: 'center', behavior: 'instant'}});
            const rect = el.getBoundingClientRect();
            if (rect.width === 0 && rect.height === 0) {{
                el.click();
                return {{fallback: true, tag: el.tagName.toLowerCase(), text: (el.innerText || '').substring(0, 100)}};
            }}
            return {{
                x: rect.x + rect.width / 2,
                y: rect.y + rect.height / 2,
                tag: el.tagName.toLowerCase(),
                text: (el.innerText || '').substring(0, 100)
            }};
        }})()
        """
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True
        })
        
        value = result.get("result", {}).get("value")
        if value is None:
            return {"success": False, "error": f"Element not found: {selector}"}
        
        # If fallback was used, element was already clicked via JS
        if value.get("fallback"):
            return {
                "success": True, "selector": selector,
                "clicked_element": {"tag": value["tag"], "text": value["text"]},
                "method": "js_fallback",
            }
        
        x, y = value["x"], value["y"]
        await asyncio.sleep(0.05)  # Brief pause after scroll
        
        # Dispatch mouse events: move → press → release
        for event_type in ["mouseMoved", "mousePressed", "mouseReleased"]:
            await self.cdp.send("Input.dispatchMouseEvent", {
                "type": event_type, "x": x, "y": y,
                "button": "left", "clickCount": 1,
            })
        
        return {
            "success": True, "selector": selector,
            "clicked_element": {"tag": value["tag"], "text": value["text"]},
        }

    # ── Type Text ───────────────────────────────────────────────

    async def type_text(self, selector: str, text: str, clear_first: bool = True) -> dict:
        """Type text into an input element.
        
        Uses native value setter + event dispatch for React/Vue/Angular
        compatibility. Falls back to execCommand for contenteditable.
        
        Args:
            selector: CSS selector of the input element.
            text: Text to type.
            clear_first: If True, clear the input before typing.
            
        Returns:
            {"success": True, "selector": selector, "typed": text}
        """
        clear_flag = "true" if clear_first else "false"
        escaped_text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n")
        
        js = f"""
        (() => {{
            const el = document.querySelector('{selector}');
            if (!el) return null;
            el.focus();
            
            // Contenteditable
            if (el.isContentEditable) {{
                if ({clear_flag}) el.textContent = '';
                document.execCommand('insertText', false, '{escaped_text}');
                return {{method: 'contenteditable', tag: el.tagName.toLowerCase()}};
            }}
            
            // Input/Textarea: native setter for React/Vue/Angular compat
            var nativeSetter = Object.getOwnPropertyDescriptor(
                el.tagName === 'TEXTAREA' 
                    ? window.HTMLTextAreaElement.prototype 
                    : window.HTMLInputElement.prototype, 
                'value'
            );
            
            if (nativeSetter && nativeSetter.set) {{
                if ({clear_flag}) {{
                    nativeSetter.set.call(el, '');
                    el.dispatchEvent(new Event('input', {{bubbles: true}}));
                }}
                nativeSetter.set.call(el, '{escaped_text}');
            }} else {{
                if ({clear_flag}) el.value = '';
                el.value = '{escaped_text}';
            }}
            
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return {{method: 'native_setter', tag: el.tagName.toLowerCase(), value: el.value}};
        }})()
        """
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True
        })
        
        value = result.get("result", {}).get("value")
        if value is None:
            return {"success": False, "error": f"Element not found: {selector}"}

        return {"success": True, "selector": selector, "typed": text, "method": value.get("method", "unknown")}

    # ── Press Key ───────────────────────────────────────────────

    async def press_key(self, key: str) -> dict:
        """Press a keyboard key (Enter, Tab, Escape, etc).
        
        Args:
            key: Key name (e.g. "Enter", "Tab", "Escape", "ArrowDown")
            
        Returns:
            {"success": True, "key": key}
        """
        key_definitions = {
            "Enter": {"key": "Enter", "code": "Enter", "keyCode": 13},
            "Tab": {"key": "Tab", "code": "Tab", "keyCode": 9},
            "Escape": {"key": "Escape", "code": "Escape", "keyCode": 27},
            "Backspace": {"key": "Backspace", "code": "Backspace", "keyCode": 8},
            "ArrowUp": {"key": "ArrowUp", "code": "ArrowUp", "keyCode": 38},
            "ArrowDown": {"key": "ArrowDown", "code": "ArrowDown", "keyCode": 40},
            "ArrowLeft": {"key": "ArrowLeft", "code": "ArrowLeft", "keyCode": 37},
            "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "keyCode": 39},
        }
        
        key_def = key_definitions.get(key, {"key": key, "code": key, "keyCode": 0})
        
        await self.cdp.send("Input.dispatchKeyEvent", {
            "type": "keyDown",
            **key_def,
            "windowsVirtualKeyCode": key_def["keyCode"],
        })
        await self.cdp.send("Input.dispatchKeyEvent", {
            "type": "keyUp",
            **key_def,
            "windowsVirtualKeyCode": key_def["keyCode"],
        })
        
        return {"success": True, "key": key}

    # ── Screenshot ──────────────────────────────────────────────

    async def screenshot(self, format: str = "png", quality: int = 80) -> dict:
        """Capture a screenshot of the current page.
        
        Args:
            format: Image format ("png" or "jpeg").
            quality: JPEG quality (1-100), ignored for PNG.
            
        Returns:
            {"success": True, "format": format, "data": base64_string, "size_kb": float}
        """
        params = {"format": format}
        if format == "jpeg":
            params["quality"] = quality
            
        result = await self.cdp.send("Page.captureScreenshot", params)
        data = result.get("data", "")
        size_kb = round(len(base64.b64decode(data)) / 1024, 1)
        
        return {
            "success": True,
            "format": format,
            "data": data,
            "size_kb": size_kb,
        }

    # ── Content Extraction ──────────────────────────────────────

    async def get_text(self, selector: str | None = None,
                       max_length: int = 0) -> dict:
        """Get the visible text content of an element or the entire page.
        
        Args:
            selector: CSS selector to scope text extraction (optional).
            max_length: Max characters to return (0 = no limit).
        
        Returns:
            {"success": True, "text": page_text, "length": char_count, "truncated": bool}
        """
        if selector:
            expr = f'(document.querySelector("{selector}")?.innerText || "")'
        else:
            expr = 'document.body.innerText'

        result = await self.cdp.send("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
        })
        text = result.get("result", {}).get("value", "")
        
        # Remove excessive blank lines
        import re
        text = re.sub(r'\n{3,}', '\n\n', text).strip()
        
        truncated = False
        if max_length > 0 and len(text) > max_length:
            text = text[:max_length] + "\n... [truncated]"
            truncated = True
        
        return {
            "success": True,
            "text": text,
            "length": len(text),
            "truncated": truncated,
        }

    async def get_html(self, selector: str | None = None) -> dict:
        """Get HTML content of an element or the entire page.
        
        Args:
            selector: CSS selector (optional, defaults to entire page).
            
        Returns:
            {"success": True, "html": html_string, "length": char_count}
        """
        if selector:
            js = f"""
            (() => {{
                const el = document.querySelector('{selector}');
                return el ? el.outerHTML : null;
            }})()
            """
        else:
            js = "document.documentElement.outerHTML"
        
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": js,
            "returnByValue": True,
        })
        html = result.get("result", {}).get("value")
        
        if html is None:
            return {"success": False, "error": f"Element not found: {selector}"}
        
        return {"success": True, "html": html, "length": len(html)}

    # ── JavaScript Evaluation ───────────────────────────────────

    async def evaluate(self, expression: str) -> dict:
        """Execute arbitrary JavaScript in the page context.
        
        Args:
            expression: JavaScript expression to evaluate.
            
        Returns:
            {"success": True, "result": return_value}
        """
        result = await self.cdp.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        })
        
        inner = result.get("result", {})
        
        if inner.get("subtype") == "error":
            return {"success": False, "error": inner.get("description", "JS error")}
        
        return {"success": True, "result": inner.get("value"), "type": inner.get("type")}

    # ── Scrolling ───────────────────────────────────────────────

    async def scroll(self, direction: str = "down", amount: int = 500) -> dict:
        """Scroll the page.
        
        Args:
            direction: "up", "down", "left", or "right"
            amount: Pixels to scroll (default 500).
            
        Returns:
            {"success": True, "direction": direction, "amount": amount, "scroll_position": {x, y}}
        """
        dx, dy = 0, 0
        if direction == "down":
            dy = amount
        elif direction == "up":
            dy = -amount
        elif direction == "right":
            dx = amount
        elif direction == "left":
            dx = -amount
        else:
            return {"success": False, "error": f"Invalid direction: {direction}. Use up/down/left/right."}

        result = await self.cdp.send("Runtime.evaluate", {
            "expression": f"window.scrollBy({dx}, {dy}); ({{x: window.scrollX, y: window.scrollY}})",
            "returnByValue": True,
        })
        
        pos = result.get("result", {}).get("value", {})
        return {"success": True, "direction": direction, "amount": amount, "scroll_position": pos}

    # ── Wait For Element ────────────────────────────────────────

    async def wait_for(self, selector: str, timeout: float = 10) -> dict:
        """Wait for an element to appear in the DOM.
        
        Args:
            selector: CSS selector to wait for.
            timeout: Max seconds to wait (default 10).
            
        Returns:
            {"success": True, "selector": selector, "found": True}
        """
        interval = 0.25
        elapsed = 0.0
        
        while elapsed < timeout:
            result = await self.cdp.send("Runtime.evaluate", {
                "expression": f"document.querySelector('{selector}') !== null",
                "returnByValue": True,
            })
            if result.get("result", {}).get("value"):
                return {"success": True, "selector": selector, "found": True}
            
            await asyncio.sleep(interval)
            elapsed += interval
        
        return {"success": False, "error": f"Element '{selector}' not found within {timeout}s"}

    # ── Tab Management ──────────────────────────────────────────

    async def get_tabs(self) -> dict:
        """Get all open browser tabs.
        
        Returns:
            {"success": True, "tabs": [{"id", "title", "url"}, ...], "count": n}
        """
        tabs = await self.cdp.get_tabs()
        tab_list = [
            {"id": t["id"], "title": t.get("title", ""), "url": t.get("url", "")}
            for t in tabs
        ]
        return {"success": True, "tabs": tab_list, "count": len(tab_list)}

    async def switch_tab(self, tab_id: str) -> dict:
        """Switch to a different browser tab.
        
        Args:
            tab_id: The tab ID (from get_tabs result).
            
        Returns:
            {"success": True, "tab_id": tab_id}
        """
        try:
            await self.cdp.connect_to_tab(tab_id)
            await self.cdp.enable_domain("Page")
            await self.cdp.enable_domain("Runtime")
            await self.cdp.enable_domain("DOM")
            await self.cdp.enable_domain("Network")
            self.cdp.on("Runtime.consoleAPICalled", self._on_console)
            self.cdp.on("Network.requestWillBeSent", self._on_request)
            self.cdp.on("Network.responseReceived", self._on_response)
            return {"success": True, "tab_id": tab_id}
        except ValueError as e:
            return {"success": False, "error": str(e)}

    # ── Console Logs ────────────────────────────────────────────

    async def get_console_logs(self, level: str | None = None, clear: bool = False) -> dict:
        """Get captured console log messages.
        
        Args:
            level: Optional filter by log level ('log', 'warn', 'error', 'info', 'debug').
            clear: If True, clear the log buffer after reading.
            
        Returns:
            {"success": True, "logs": [...], "count": n}
        """
        if level:
            logs = [l for l in self._console_logs if l["type"] == level]
        else:
            logs = list(self._console_logs)
        
        if clear:
            self._console_logs.clear()
        
        return {"success": True, "logs": logs, "count": len(logs)}

    async def clear_console_logs(self) -> dict:
        """Clear the console log buffer.
        
        Returns:
            {"success": True, "cleared": n}
        """
        count = len(self._console_logs)
        self._console_logs.clear()
        return {"success": True, "cleared": count}

    # ── Network Logs ────────────────────────────────────────────

    async def get_network_logs(self, url_filter: str | None = None, 
                                method_filter: str | None = None, 
                                clear: bool = False) -> dict:
        """Get captured network request/response logs.
        
        Args:
            url_filter: Optional substring filter for URLs.
            method_filter: Optional filter by HTTP method (GET, POST, etc).
            clear: If True, clear the log buffer after reading.
            
        Returns:
            {"success": True, "requests": [...], "count": n}
        """
        logs = self._network_logs
        
        if url_filter:
            logs = [l for l in logs if url_filter in l["url"]]
        if method_filter:
            logs = [l for l in logs if l["method"].upper() == method_filter.upper()]
        
        result = list(logs)
        
        if clear:
            self._network_logs.clear()
        
        return {"success": True, "requests": result, "count": len(result)}

    async def clear_network_logs(self) -> dict:
        """Clear the network log buffer.
        
        Returns:
            {"success": True, "cleared": n}
        """
        count = len(self._network_logs)
        self._network_logs.clear()
        return {"success": True, "cleared": count}

    # ── Element Finding ─────────────────────────────────────────

    async def find_elements(self, query: str, role: str | None = None,
                            max_results: int = 20) -> dict:
        """Search for elements by text content and/or accessibility role.
        
        Uses the accessibility tree to find matching elements.
        Auto-refreshes the snapshot if no refs exist yet.
        
        Args:
            query: Text to search for (case-insensitive substring match).
            role: Optional role filter (button, link, textbox, heading, etc).
            max_results: Maximum results to return.
            
        Returns:
            {"success": True, "elements": [...], "count": n}
        """
        # Only fetch snapshot if no refs exist (avoids double AX tree fetch)
        if not self._ref_map:
            await self.get_page_snapshot()
        
        # Single AX tree fetch (reusing data if snapshot already populated refs)
        result = await self.cdp.send("Accessibility.getFullAXTree")
        nodes = result.get("nodes", [])
        
        # Build reverse map: backendDOMNodeId -> ref for fast lookup
        backend_to_ref: dict[int, int] = {bid: r for r, bid in self._ref_map.items()}
        
        matches = []
        query_lower = query.lower() if query else ""
        
        for node in nodes:
            if node.get("ignored", False):
                continue
            
            role_obj = node.get("role", {})
            node_role = role_obj.get("value", "") if isinstance(role_obj, dict) else ""
            
            name_obj = node.get("name", {})
            node_name = name_obj.get("value", "") if isinstance(name_obj, dict) else ""
            
            value_obj = node.get("value", {})
            node_value = value_obj.get("value", "") if isinstance(value_obj, dict) else ""
            
            # Apply role filter
            if role and node_role.lower() != role.lower():
                continue
            
            # Apply text filter
            text_match = (query_lower in node_name.lower() or 
                         query_lower in node_value.lower()) if query_lower else True
            if not text_match:
                continue
            
            # Skip noise
            if node_role in self.SKIP_ROLES:
                continue
            
            # Fast ref lookup via reverse map
            backend_id = node.get("backendDOMNodeId")
            ref = backend_to_ref.get(backend_id) if backend_id is not None else None
            
            matches.append({
                "role": node_role,
                "name": node_name[:200],
                "value": node_value[:100] if node_value else None,
                "ref": ref,
                "interactive": node_role in self.INTERACTIVE_ROLES,
            })
            
            if len(matches) >= max_results:
                break
        
        return {"success": True, "elements": matches, "count": len(matches)}

    # ── Fill Form ────────────────────────────────────────────────

    async def fill_form(self, fields: list[dict]) -> dict:
        """Fill multiple form fields in a single call.
        
        Each field specifies a ref and value. Uses the framework-compatible
        type_ref internally for each field.
        
        Args:
            fields: List of {"ref": N, "value": "text"} dicts.
            
        Returns:
            {"success": True, "filled": N, "results": [...]}
        """
        results = []
        for field in fields:
            ref = field.get("ref")
            value = field.get("value", "")
            if ref is None:
                results.append({"ref": None, "success": False, "error": "Missing ref"})
                continue
            r = await self.type_ref(ref, value, clear_first=True)
            results.append({"ref": ref, "success": r.get("success", False), "value": value})
        
        filled = sum(1 for r in results if r["success"])
        return {"success": filled > 0, "filled": filled, "total": len(fields), "results": results}

    # ── Drag and Drop ────────────────────────────────────────────

    async def drag_drop(self, from_ref: int, to_ref: int) -> dict:
        """Drag an element and drop it onto another element.
        
        Args:
            from_ref: Ref of the element to drag.
            to_ref: Ref of the drop target element.
            
        Returns:
            {"success": True, "from_ref": N, "to_ref": M}
        """
        for ref_num, label in [(from_ref, "from_ref"), (to_ref, "to_ref")]:
            if ref_num not in self._ref_map:
                return {"success": False, "error": f"{label} {ref_num} not found."}
        
        try:
            # Get coordinates for both elements
            coords = {}
            for ref_num, key in [(from_ref, "from"), (to_ref, "to")]:
                backend_id = self._ref_map[ref_num]
                resolve = await self.cdp.send("DOM.resolveNode", {"backendNodeId": backend_id})
                object_id = resolve.get("object", {}).get("objectId")
                if not object_id:
                    return {"success": False, "error": f"Cannot resolve ref {ref_num}"}
                
                # Scroll into view
                await self.cdp.send("Runtime.callFunctionOn", {
                    "objectId": object_id,
                    "functionDeclaration": "function() { this.scrollIntoViewIfNeeded(); }",
                })
                await asyncio.sleep(0.05)
                
                box = await self.cdp.send("Runtime.callFunctionOn", {
                    "objectId": object_id,
                    "functionDeclaration": """function() {
                        const r = this.getBoundingClientRect();
                        return {x: r.x + r.width/2, y: r.y + r.height/2};
                    }""",
                    "returnByValue": True,
                })
                coords[key] = box.get("result", {}).get("value", {})
            
            fx, fy = coords["from"]["x"], coords["from"]["y"]
            tx, ty = coords["to"]["x"], coords["to"]["y"]
            
            # Mouse down on source
            await self.cdp.send("Input.dispatchMouseEvent", {
                "type": "mousePressed", "x": fx, "y": fy,
                "button": "left", "clickCount": 1,
            })
            await asyncio.sleep(0.1)
            
            # Move to target (with intermediate steps for smooth drag)
            steps = 5
            for i in range(1, steps + 1):
                mx = fx + (tx - fx) * i / steps
                my = fy + (ty - fy) * i / steps
                await self.cdp.send("Input.dispatchMouseEvent", {
                    "type": "mouseMoved", "x": mx, "y": my,
                    "button": "left",
                })
                await asyncio.sleep(0.03)
            
            # Mouse up on target
            await self.cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseReleased", "x": tx, "y": ty,
                "button": "left", "clickCount": 1,
            })
            
            return {"success": True, "from_ref": from_ref, "to_ref": to_ref}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def hover(self, ref: int) -> dict:
        """Hover over an element by ref number (triggers tooltips, menus).
        
        Args:
            ref: Element ref from get_page_snapshot.
            
        Returns:
            {"success": True, "ref": ref}
        """
        if ref not in self._ref_map:
            return {"success": False, "error": f"Ref {ref} not found."}
        
        backend_node_id = self._ref_map[ref]
        try:
            resolve = await self.cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
            object_id = resolve.get("object", {}).get("objectId")
            if not object_id:
                return {"success": False, "error": f"Cannot resolve ref {ref}"}
            
            # Scroll into view
            await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": "function() { this.scrollIntoViewIfNeeded(); }",
            })
            await asyncio.sleep(0.1)
            
            # Get center coordinates
            box_result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": """function() {
                    const r = this.getBoundingClientRect();
                    return {x: r.x + r.width/2, y: r.y + r.height/2};
                }""",
                "returnByValue": True,
            })
            coords = box_result.get("result", {}).get("value", {})
            
            await self.cdp.send("Input.dispatchMouseEvent", {
                "type": "mouseMoved", "x": coords["x"], "y": coords["y"],
            })
            await asyncio.sleep(0.3)  # Wait for tooltip/menu to appear
            
            return {"success": True, "ref": ref}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Select Dropdown Option ──────────────────────────────────

    async def select_option(self, ref: int, value: str = "",
                            label: str = "") -> dict:
        """Select an option from a <select> dropdown by ref.
        
        Args:
            ref: Ref of the <select> element.
            value: Option value attribute to select.
            label: Option visible text to select (used if value is empty).
            
        Returns:
            {"success": True, "ref": ref, "selected": value_or_label}
        """
        if ref not in self._ref_map:
            return {"success": False, "error": f"Ref {ref} not found."}
        
        backend_node_id = self._ref_map[ref]
        try:
            resolve = await self.cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
            object_id = resolve.get("object", {}).get("objectId")
            if not object_id:
                return {"success": False, "error": f"Cannot resolve ref {ref}"}
            
            selector_by = "value" if value else "label"
            match_val = value if value else label
            
            js = f"""function() {{
                const options = Array.from(this.options || []);
                const match = options.find(o => 
                    o.{selector_by} === {repr(match_val)} || 
                    o.text.includes({repr(match_val)})
                );
                if (match) {{
                    this.value = match.value;
                    this.dispatchEvent(new Event('change', {{bubbles: true}}));
                    return {{selected: match.text, value: match.value}};
                }}
                return null;
            }}"""
            
            result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": js,
                "returnByValue": True,
            })
            val = result.get("result", {}).get("value")
            if val:
                return {"success": True, "ref": ref, "selected": val}
            return {"success": False, "error": f"Option '{match_val}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Browser History Navigation ──────────────────────────────

    async def go_back(self) -> dict:
        """Navigate back in browser history.
        
        Returns:
            {"success": True, "url": new_url}
        """
        await self.cdp.send("Runtime.evaluate", {
            "expression": "window.history.back()",
        })
        await asyncio.sleep(1)
        r = await self.cdp.send("Runtime.evaluate", {
            "expression": "window.location.href",
            "returnByValue": True,
        })
        url = r.get("result", {}).get("value", "")
        return {"success": True, "url": url}

    async def go_forward(self) -> dict:
        """Navigate forward in browser history.
        
        Returns:
            {"success": True, "url": new_url}
        """
        await self.cdp.send("Runtime.evaluate", {
            "expression": "window.history.forward()",
        })
        await asyncio.sleep(1)
        r = await self.cdp.send("Runtime.evaluate", {
            "expression": "window.location.href",
            "returnByValue": True,
        })
        url = r.get("result", {}).get("value", "")
        return {"success": True, "url": url}

    # ── Dialog Handling ─────────────────────────────────────────

    async def handle_dialog(self, accept: bool = True, text: str = "") -> dict:
        """Handle JavaScript alert/confirm/prompt dialogs.
        
        Auto-enables dialog interception on first call.
        
        Args:
            accept: True to click OK/Accept, False to Cancel/Dismiss.
            text: Text to enter for prompt dialogs.
            
        Returns:
            {"success": True, "action": "accepted"/"dismissed"}
        """
        try:
            params: dict = {"accept": accept}
            if text:
                params["promptText"] = text
            await self.cdp.send("Page.handleJavaScriptDialog", params)
            action = "accepted" if accept else "dismissed"
            return {"success": True, "action": action}
        except Exception as e:
            return {"success": False, "error": f"No dialog to handle: {str(e)}"}

    # ── Cookie Management ───────────────────────────────────────

    async def get_cookies(self, url: str = "") -> dict:
        """Get all cookies, optionally filtered by URL.
        
        Args:
            url: Optional URL to filter cookies for.
            
        Returns:
            {"success": True, "cookies": [...], "count": n}
        """
        params = {}
        if url:
            params["urls"] = [url]
        result = await self.cdp.send("Network.getCookies", params)
        cookies = result.get("cookies", [])
        # Simplify cookie data
        simple = [{
            "name": c.get("name"),
            "value": c.get("value"),
            "domain": c.get("domain"),
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
        } for c in cookies]
        return {"success": True, "cookies": simple, "count": len(simple)}

    async def set_cookie(self, name: str, value: str, domain: str,
                         path: str = "/", http_only: bool = False,
                         secure: bool = False) -> dict:
        """Set a browser cookie.
        
        Args:
            name: Cookie name.
            value: Cookie value.
            domain: Domain for the cookie.
            path: Cookie path (default "/").
            http_only: HttpOnly flag.
            secure: Secure flag.
            
        Returns:
            {"success": True, "cookie": name}
        """
        await self.cdp.send("Network.setCookie", {
            "name": name, "value": value, "domain": domain,
            "path": path, "httpOnly": http_only, "secure": secure,
        })
        return {"success": True, "cookie": name}

    # ── Element State Check ─────────────────────────────────────

    async def check_element(self, ref: int) -> dict:
        """Check if an element exists, is visible, enabled, and get its properties.
        
        Args:
            ref: Element ref from page snapshot.
            
        Returns:
            {"success": True, "ref": ref, "exists": bool, "visible": bool, 
             "enabled": bool, "tag": str, "text": str}
        """
        if ref not in self._ref_map:
            return {"success": True, "ref": ref, "exists": False,
                    "visible": False, "enabled": False, "tag": "", "text": ""}
        
        backend_node_id = self._ref_map[ref]
        try:
            resolve = await self.cdp.send("DOM.resolveNode", {"backendNodeId": backend_node_id})
            object_id = resolve.get("object", {}).get("objectId")
            if not object_id:
                return {"success": True, "ref": ref, "exists": False,
                        "visible": False, "enabled": False, "tag": "", "text": ""}
            
            js = """function() {
                const rect = this.getBoundingClientRect();
                const style = window.getComputedStyle(this);
                return {
                    exists: true,
                    visible: rect.width > 0 && rect.height > 0 && 
                             style.display !== 'none' && style.visibility !== 'hidden',
                    enabled: !this.disabled,
                    tag: this.tagName?.toLowerCase() || '',
                    text: (this.innerText || this.textContent || '').substring(0, 200),
                    type: this.type || '',
                    href: this.href || '',
                    checked: this.checked || false,
                };
            }"""
            
            result = await self.cdp.send("Runtime.callFunctionOn", {
                "objectId": object_id,
                "functionDeclaration": js,
                "returnByValue": True,
            })
            val = result.get("result", {}).get("value", {})
            val["ref"] = ref
            val["success"] = True
            return val
        except Exception:
            return {"success": True, "ref": ref, "exists": False,
                    "visible": False, "enabled": False, "tag": "", "text": ""}

    # ── Structured Data Extraction ──────────────────────────────

    async def extract_data(self, instruction: str, selector: str = "body") -> dict:
        """Extract structured data from the page based on natural language instruction.
        
        Extracts text content organized by semantic structure (headings, lists,
        tables, links) from the specified element.
        
        Args:
            instruction: What data to extract (e.g. "product prices", "all links").
            selector: CSS selector to scope extraction (default: entire page).
            
        Returns:
            {"success": True, "data": {...}, "instruction": instruction}
        """
        js = f"""(() => {{
            const el = document.querySelector({repr(selector)}) || document.body;
            const data = {{}};
            
            // Extract headings
            const headings = Array.from(el.querySelectorAll('h1,h2,h3,h4,h5,h6'));
            if (headings.length) data.headings = headings.map(h => ({{
                level: parseInt(h.tagName[1]), text: h.innerText.trim()
            }}));
            
            // Extract links
            const links = Array.from(el.querySelectorAll('a[href]'));
            if (links.length) data.links = links.slice(0, 50).map(a => ({{
                text: a.innerText.trim().substring(0, 100),
                href: a.href
            }})).filter(l => l.text);
            
            // Extract images
            const imgs = Array.from(el.querySelectorAll('img'));
            if (imgs.length) data.images = imgs.slice(0, 30).map(i => ({{
                alt: i.alt || '', src: i.src
            }}));
            
            // Extract tables
            const tables = Array.from(el.querySelectorAll('table'));
            if (tables.length) data.tables = tables.slice(0, 5).map(t => {{
                const rows = Array.from(t.querySelectorAll('tr'));
                return rows.slice(0, 30).map(r => 
                    Array.from(r.querySelectorAll('td,th')).map(c => c.innerText.trim().substring(0, 100))
                );
            }});
            
            // Extract form inputs
            const inputs = Array.from(el.querySelectorAll('input,select,textarea'));
            if (inputs.length) data.form_fields = inputs.map(i => ({{
                type: i.type || i.tagName.toLowerCase(),
                name: i.name || i.id || '',
                value: i.value || '',
                placeholder: i.placeholder || '',
            }}));
            
            // Extract lists
            const lists = Array.from(el.querySelectorAll('ul,ol'));
            if (lists.length) data.lists = lists.slice(0, 10).map(l => 
                Array.from(l.querySelectorAll('li')).slice(0, 20).map(i => i.innerText.trim().substring(0, 200))
            );
            
            // Plain text summary
            data.text_content = el.innerText?.substring(0, 2000) || '';
            
            return data;
        }})()"""
        
        try:
            result = await self.cdp.send("Runtime.evaluate", {
                "expression": js, "returnByValue": True,
            })
            data = result.get("result", {}).get("value", {})
            return {"success": True, "data": data, "instruction": instruction}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ── Page Error Detection (Auto-Debug) ───────────────────────

    async def get_page_errors(self) -> dict:
        """Detect JavaScript errors, failed resources, and page issues.
        
        Combines console errors with runtime exceptions for debugging.
        
        Returns:
            {"success": True, "errors": [...], "warnings": [...], 
             "failed_requests": [...], "error_count": n}
        """
        # Console errors
        error_logs = [l for l in self._console_logs if l.get("level") in ("error",)]
        warning_logs = [l for l in self._console_logs if l.get("level") in ("warning",)]
        
        # Check for uncaught exceptions via JS
        js_errors_result = await self.cdp.send("Runtime.evaluate", {
            "expression": """(() => {
                const errors = window.__nodewalker_errors || [];
                return errors.slice(-20);
            })()""",
            "returnByValue": True,
        })
        js_errors = js_errors_result.get("result", {}).get("value", []) or []
        
        # Install error catcher if not already
        await self.cdp.send("Runtime.evaluate", {
            "expression": """
                if (!window.__nodewalker_errors) {
                    window.__nodewalker_errors = [];
                    window.addEventListener('error', (e) => {
                        window.__nodewalker_errors.push({
                            message: e.message, source: e.filename,
                            line: e.lineno, col: e.colno, time: Date.now()
                        });
                        if (window.__nodewalker_errors.length > 50) 
                            window.__nodewalker_errors.shift();
                    });
                    window.addEventListener('unhandledrejection', (e) => {
                        window.__nodewalker_errors.push({
                            message: 'Unhandled Promise: ' + String(e.reason),
                            time: Date.now()
                        });
                    });
                }
            """,
        })
        
        # Failed network requests
        failed = [l for l in self._network_logs 
                  if l.get("status") and l["status"] >= 400]
        
        return {
            "success": True,
            "errors": error_logs[-20:],
            "warnings": warning_logs[-10:],
            "js_exceptions": js_errors,
            "failed_requests": [{
                "url": f.get("url", "")[:200],
                "method": f.get("method"),
                "status": f.get("status"),
            } for f in failed[-20:]],
            "error_count": len(error_logs) + len(js_errors) + len(failed),
        }

    # ── Wait for Navigation ─────────────────────────────────────

    async def wait_for_navigation(self, timeout: float = 10) -> dict:
        """Wait for page navigation/load to complete.
        
        Useful after clicking links or submitting forms.
        
        Args:
            timeout: Max seconds to wait.
            
        Returns:
            {"success": True, "url": current_url, "title": page_title}
        """
        deadline = asyncio.get_event_loop().time() + timeout
        prev_url = ""
        
        # Get current URL
        r = await self.cdp.send("Runtime.evaluate", {
            "expression": "window.location.href", "returnByValue": True,
        })
        prev_url = r.get("result", {}).get("value", "")
        
        # Poll until URL changes or document is ready
        while asyncio.get_event_loop().time() < deadline:
            try:
                ready_result = await self.cdp.send("Runtime.evaluate", {
                    "expression": "({ready: document.readyState, url: window.location.href, title: document.title})",
                    "returnByValue": True,
                })
                state = ready_result.get("result", {}).get("value", {})
                
                if state.get("ready") == "complete":
                    return {
                        "success": True,
                        "url": state.get("url", ""),
                        "title": state.get("title", ""),
                    }
            except Exception:
                pass  # Page may be mid-navigation
            
            await asyncio.sleep(0.3)
        
        return {"success": False, "error": f"Navigation timeout after {timeout}s"}
