# NodeWalker – Tool Reference

This document describes all available browser control tools.
An AI agent reading this file will have complete knowledge of how to use NodeWalker.

## Server

**Base URL:** `http://localhost:8585`

All tools are called via `POST /execute` with JSON body:
```json
{"tool": "<tool_name>", "arguments": {<arguments>}}
```

Every response follows this format:
```json
{"success": true/false, "result": {...}, "error": "message if failed"}
```

---

## Tools

### navigate
Navigate the browser to a URL and wait for the page to load.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| url | string | ✅ | URL to navigate to |

**Example:** `{"tool": "navigate", "arguments": {"url": "https://google.com"}}`
**Returns:** `{"success": true, "url": "...", "title": "Google"}`

---

### click
Click an element using a CSS selector.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| selector | string | ✅ | CSS selector (e.g. `#btn`, `.link`, `button`) |

**Example:** `{"tool": "click", "arguments": {"selector": "#search-btn"}}`
**Returns:** `{"success": true, "selector": "...", "clicked_element": {"tag": "button", "text": "Search"}}`

---

### type_text
Type text into an input field.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| selector | string | ✅ | CSS selector of the input |
| text | string | ✅ | Text to type |
| clear_first | boolean | ❌ | Clear input before typing (default: true) |

**Example:** `{"tool": "type_text", "arguments": {"selector": "#search-input", "text": "hello world"}}`

---

### press_key
Press a keyboard key.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| key | string | ✅ | Key name: `Enter`, `Tab`, `Escape`, `Backspace`, `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight` |

**Example:** `{"tool": "press_key", "arguments": {"key": "Enter"}}`

---

### screenshot
Capture a screenshot of the current page.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| format | string | ❌ | `png` or `jpeg` (default: png) |
| quality | integer | ❌ | JPEG quality 1-100 (default: 80) |

**Example:** `{"tool": "screenshot", "arguments": {}}`
**Returns:** `{"success": true, "format": "png", "data": "<base64>", "size_kb": 145.2}`

---

### get_text
Get the visible text content of the entire page (no HTML tags).

**Example:** `{"tool": "get_text", "arguments": {}}`
**Returns:** `{"success": true, "text": "Page content here...", "length": 1234}`

---

### get_html
Get HTML source of a specific element or the entire page.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| selector | string | ❌ | CSS selector (omit for entire page) |

**Example:** `{"tool": "get_html", "arguments": {"selector": "#main"}}`

---

### evaluate
Execute arbitrary JavaScript in the page context.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| expression | string | ✅ | JavaScript expression to evaluate |

**Example:** `{"tool": "evaluate", "arguments": {"expression": "document.title"}}`
**Returns:** `{"success": true, "result": "Page Title", "type": "string"}`

---

### scroll
Scroll the page in a given direction.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| direction | string | ✅ | `up`, `down`, `left`, `right` |
| amount | integer | ❌ | Pixels to scroll (default: 500) |

**Example:** `{"tool": "scroll", "arguments": {"direction": "down", "amount": 300}}`

---

### wait_for
Wait for an element to appear in the DOM.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| selector | string | ✅ | CSS selector to wait for |
| timeout | number | ❌ | Max seconds to wait (default: 10) |

**Example:** `{"tool": "wait_for", "arguments": {"selector": "#results", "timeout": 5}}`

---

### get_tabs
List all open browser tabs.

**Example:** `{"tool": "get_tabs", "arguments": {}}`
**Returns:** `{"success": true, "tabs": [{"id": "...", "title": "Google", "url": "..."}], "count": 3}`

---

### switch_tab
Switch control to a different browser tab.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| tab_id | string | ✅ | Tab ID from `get_tabs` result |

**Example:** `{"tool": "switch_tab", "arguments": {"tab_id": "ABC123"}}`
