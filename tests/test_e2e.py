"""Quick E2E test for NodeWalker API."""
import urllib.request
import json

BASE = "http://localhost:8586"

def api(endpoint, data=None):
    if data:
        req = urllib.request.Request(
            f"{BASE}{endpoint}",
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
    else:
        req = f"{BASE}{endpoint}"
    return json.loads(urllib.request.urlopen(req).read())

print("NodeWalker E2E Test")
print("=" * 40)

# 1. Health
print("\n1. Health check")
r = api("/health")
print(f"   Status: {r['status']}, Connected: {r['connected']}")

# 2. Tools
print("\n2. Tool schemas")
tools = api("/tools")
names = [t["function"]["name"] for t in tools]
print(f"   {len(tools)} tools: {', '.join(names)}")

# 3. Navigate
print("\n3. Navigate to example.com")
r = api("/execute", {"tool": "navigate", "arguments": {"url": "https://example.com"}})
print(f"   Success: {r['success']}, Title: {r['result'].get('title', 'N/A')}")

# 4. Get text
print("\n4. Get page text")
r = api("/execute", {"tool": "get_text", "arguments": {}})
print(f"   Success: {r['success']}, Length: {r['result']['length']}")
preview = r['result']['text'][:100].replace('\n', ' ')
print(f"   Preview: {preview}...")

# 5. Screenshot
print("\n5. Screenshot")
r = api("/execute", {"tool": "screenshot", "arguments": {"format": "jpeg", "quality": 50}})
print(f"   Success: {r['success']}, Size: {r['result']['size_kb']} KB")

# 6. Evaluate JS
print("\n6. Evaluate JS")
r = api("/execute", {"tool": "evaluate", "arguments": {"expression": "document.title"}})
print(f"   Success: {r['success']}, Result: {r['result']['result']}")

# 7. Get tabs
print("\n7. Get tabs")
r = api("/execute", {"tool": "get_tabs", "arguments": {}})
print(f"   Success: {r['success']}, Count: {r['result']['count']}")

# 8. Scroll
print("\n8. Scroll down")
r = api("/execute", {"tool": "scroll", "arguments": {"direction": "down", "amount": 200}})
print(f"   Success: {r['success']}")

print("\n" + "=" * 40)
print("All tests completed!")
