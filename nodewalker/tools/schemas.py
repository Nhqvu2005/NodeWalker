"""
Tool Schemas - OpenAI-compatible function calling definitions.

These schemas describe every browser action in standard JSON Schema format.
Any AI that supports function/tool calling can use these directly.
"""

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate the browser to a URL. Auto-prepends https:// if missing. Waits for full load.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to (e.g. 'https://example.com')"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click an element on the page using a CSS selector. Returns info about the clicked element.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element to click (e.g. '#submit-btn', '.nav-link', 'button[type=submit]')"
                    }
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_text",
            "description": "Type text into an input field. Focuses the element first, optionally clears existing text, then types character by character.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the input element (e.g. '#username', 'input[name=email]')"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type into the input"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "description": "Whether to clear existing text before typing (default: true)"
                    }
                },
                "required": ["selector", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "press_key",
            "description": "Press a keyboard key. Useful for submitting forms (Enter), navigating (Tab), or closing dialogs (Escape).",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {
                        "type": "string",
                        "description": "Key name: 'Enter', 'Tab', 'Escape', 'Backspace', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'",
                        "enum": ["Enter", "Tab", "Escape", "Backspace", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"]
                    }
                },
                "required": ["key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot",
            "description": "Capture a screenshot of the current page. Returns the image as a base64-encoded string.",
            "parameters": {
                "type": "object",
                "properties": {
                    "format": {
                        "type": "string",
                        "description": "Image format: 'png' (lossless) or 'jpeg' (smaller file). Default: 'png'",
                        "enum": ["png", "jpeg"]
                    },
                    "quality": {
                        "type": "integer",
                        "description": "JPEG quality 1-100 (ignored for PNG). Default: 80",
                        "minimum": 1,
                        "maximum": 100
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_text",
            "description": "Get the visible text content of an element or the entire page. Supports scoping by CSS selector and length limiting to reduce token usage.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to scope extraction (optional, omit for full page). e.g. 'main', 'article', '#content'"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum characters to return (default: 0 = unlimited). Recommended: 2000-4000 for token efficiency.",
                        "minimum": 0
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_html",
            "description": "Get the HTML source of a specific element or the entire page.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector of the element (optional, omit for entire page)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate",
            "description": "Execute arbitrary JavaScript code in the browser page context. The expression is evaluated and the return value is sent back.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "JavaScript expression to evaluate (e.g. 'document.title', '2 + 2', 'localStorage.getItem(\"key\")')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scroll",
            "description": "Scroll the page in a given direction by a specified amount of pixels.",
            "parameters": {
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "description": "Scroll direction",
                        "enum": ["up", "down", "left", "right"]
                    },
                    "amount": {
                        "type": "integer",
                        "description": "Pixels to scroll (default: 500)",
                        "minimum": 1
                    }
                },
                "required": ["direction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for",
            "description": "Wait for an element to appear in the DOM. Polls every 250ms until found or timeout.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector to wait for (e.g. '#result', '.loading-done')"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Maximum seconds to wait (default: 10)",
                        "minimum": 0.5,
                        "maximum": 60
                    }
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_tabs",
            "description": "List all open browser tabs with their IDs, titles, and URLs.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "switch_tab",
            "description": "Switch browser control to a different tab. Use get_tabs first to find the tab ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tab_id": {
                        "type": "string",
                        "description": "The tab ID to switch to (obtained from get_tabs)"
                    }
                },
                "required": ["tab_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_console_logs",
            "description": "Get captured console.log/warn/error messages from the browser. Logs are collected automatically in the background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "level": {
                        "type": "string",
                        "description": "Filter by log level (optional). Omit to get all logs.",
                        "enum": ["log", "warn", "error", "info", "debug"]
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "Clear the log buffer after reading (default: false)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_console_logs",
            "description": "Clear all captured console log messages.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_network_logs",
            "description": "Get captured network request/response logs. Each entry includes method, URL, status code, and MIME type. Logs are collected automatically in the background.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url_filter": {
                        "type": "string",
                        "description": "Filter requests by URL substring (optional, e.g. '/api/' or '.json')"
                    },
                    "method_filter": {
                        "type": "string",
                        "description": "Filter by HTTP method (optional, e.g. 'GET', 'POST')"
                    },
                    "clear": {
                        "type": "boolean",
                        "description": "Clear the log buffer after reading (default: false)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_network_logs",
            "description": "Clear all captured network request/response logs.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_snapshot",
            "description": "Get an accessibility tree snapshot of the page with [ref=N] tags on interactive elements. Use click_ref/type_ref with these ref numbers. Set compact=true to dramatically reduce output size (shows only interactive elements, headings, landmarks, images).",
            "parameters": {
                "type": "object",
                "properties": {
                    "max_depth": {
                        "type": "integer",
                        "description": "Maximum tree depth (default: 15)",
                        "minimum": 1,
                        "maximum": 30
                    },
                    "compact": {
                        "type": "boolean",
                        "description": "If true, only show interactive elements + headings + landmarks + images. Reduces tokens by 50-80%%. Default: false."
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click_ref",
            "description": "Click an element by its [ref=N] number from a page snapshot. More reliable than CSS selectors. Call get_page_snapshot first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "integer",
                        "description": "The ref number from the page snapshot (e.g. 3)"
                    }
                },
                "required": ["ref"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "type_ref",
            "description": "Type text into an input element by its [ref=N] number from a page snapshot. More reliable than CSS selectors. Call get_page_snapshot first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {
                        "type": "integer",
                        "description": "The ref number of the input element from the page snapshot"
                    },
                    "text": {
                        "type": "string",
                        "description": "The text to type"
                    },
                    "clear_first": {
                        "type": "boolean",
                        "description": "Clear existing text before typing (default: true)"
                    },
                    "press_enter": {
                        "type": "boolean",
                        "description": "Press Enter after typing (default: false)"
                    }
                },
                "required": ["ref", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "find_elements",
            "description": "Search for elements by text content and/or accessibility role. Returns matching elements with their ref numbers for interaction.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Text to search for (case-insensitive)"},
                    "role": {"type": "string", "description": "Filter by role: button, link, textbox, heading, etc."},
                    "max_results": {"type": "integer", "description": "Max results (default 20)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "hover",
            "description": "Hover over an element by ref number. Triggers tooltips, dropdown menus, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {"type": "integer", "description": "Element ref from page snapshot"}
                },
                "required": ["ref"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "select_option",
            "description": "Select an option from a <select> dropdown by ref. Use value or label to pick.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {"type": "integer", "description": "Ref of the <select> element"},
                    "value": {"type": "string", "description": "Option value attribute"},
                    "label": {"type": "string", "description": "Option visible text (used if value empty)"}
                },
                "required": ["ref"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "go_back",
            "description": "Navigate back in browser history (like clicking the Back button).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "go_forward",
            "description": "Navigate forward in browser history (like clicking the Forward button).",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "handle_dialog",
            "description": "Handle JavaScript alert/confirm/prompt dialogs. Accept or dismiss them.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accept": {"type": "boolean", "description": "True=OK, False=Cancel (default True)"},
                    "text": {"type": "string", "description": "Text for prompt dialogs"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cookies",
            "description": "Get all browser cookies, optionally filtered by URL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Optional URL to filter cookies"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_cookie",
            "description": "Set a browser cookie with name, value, and domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Cookie name"},
                    "value": {"type": "string", "description": "Cookie value"},
                    "domain": {"type": "string", "description": "Cookie domain"},
                    "path": {"type": "string", "description": "Cookie path (default '/')"},
                    "http_only": {"type": "boolean", "description": "HttpOnly flag"},
                    "secure": {"type": "boolean", "description": "Secure flag"}
                },
                "required": ["name", "value", "domain"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_element",
            "description": "Check element state: exists, visible, enabled, tag, text, etc. Use ref from snapshot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ref": {"type": "integer", "description": "Element ref from page snapshot"}
                },
                "required": ["ref"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_data",
            "description": "Extract structured data from the page: headings, links, images, tables, forms, lists. Good for scraping and analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "instruction": {"type": "string", "description": "What to extract (e.g. 'product prices')"},
                    "selector": {"type": "string", "description": "CSS selector scope (default 'body')"}
                },
                "required": ["instruction"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_errors",
            "description": "Auto-detect page issues: JS errors, console errors, failed network requests. Essential for debugging.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "wait_for_navigation",
            "description": "Wait for page load to complete after clicking a link or submitting a form.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timeout": {"type": "number", "description": "Max seconds to wait (default 10)"}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill_form",
            "description": "Fill multiple form fields in one call. Each field is {ref, value}. Framework-compatible (React/Vue/Angular).",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "array",
                        "description": "List of {\"ref\": N, \"value\": \"text\"} objects",
                        "items": {
                            "type": "object",
                            "properties": {
                                "ref": {"type": "integer", "description": "Element ref from snapshot"},
                                "value": {"type": "string", "description": "Value to fill"}
                            },
                            "required": ["ref", "value"]
                        }
                    }
                },
                "required": ["fields"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "drag_drop",
            "description": "Drag an element and drop it onto another element. Both identified by ref numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "from_ref": {"type": "integer", "description": "Ref of element to drag"},
                    "to_ref": {"type": "integer", "description": "Ref of drop target"}
                },
                "required": ["from_ref", "to_ref"]
            }
        }
    },
]


def get_tool_schemas() -> list[dict]:
    """Return all tool schemas in OpenAI function calling format.
    
    Can be passed directly to:
    - OpenAI: openai.chat.completions.create(tools=get_tool_schemas())
    - Anthropic: converted with minimal transformation
    - Any MCP-compatible client
    """
    return TOOL_SCHEMAS


def get_tool_names() -> list[str]:
    """Return just the names of all available tools."""
    return [t["function"]["name"] for t in TOOL_SCHEMAS]


def get_tool_summary() -> str:
    """Return a human-readable summary of all tools (for AI system prompts)."""
    lines = ["Available browser control tools:"]
    for tool in TOOL_SCHEMAS:
        func = tool["function"]
        params = func["parameters"].get("properties", {})
        param_str = ", ".join(
            f"{k}: {v.get('type', 'any')}" for k, v in params.items()
        )
        lines.append(f"  - {func['name']}({param_str}): {func['description']}")
    return "\n".join(lines)
