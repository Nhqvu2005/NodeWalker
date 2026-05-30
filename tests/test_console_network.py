"""Test console and network monitoring tools."""
import urllib.request
import json
import time

BASE = "http://localhost:8587"

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

print("Console & Network Tools Test")
print("=" * 50)

# Verify 16 tools are available
tools = api("/tools")
names = [t["function"]["name"] for t in tools]
print(f"\n1. Tool count: {len(tools)} (expected 16)")
for n in names:
    print(f"   - {n}")

# Clear logs first
api("/execute", {"tool": "clear_console_logs", "arguments": {}})
api("/execute", {"tool": "clear_network_logs", "arguments": {}})

# Navigate (this will generate network requests)
print("\n2. Navigate to example.com (generates network traffic)")
r = api("/execute", {"tool": "navigate", "arguments": {"url": "https://example.com"}})
print(f"   Navigate: {r['success']}")
time.sleep(1)

# Check network logs
print("\n3. Get network logs")
r = api("/execute", {"tool": "get_network_logs", "arguments": {}})
print(f"   Success: {r['success']}, Count: {r['result']['count']}")
for req_entry in r['result']['requests'][:5]:
    url = req_entry['url'][:80]
    status = req_entry.get('status', '?')
    method = req_entry.get('method', '?')
    print(f"   {method} {status} {url}")

# Inject console.log via evaluate and then read it
print("\n4. Inject console.log via evaluate")
api("/execute", {"tool": "evaluate", "arguments": {"expression": "console.log('Hello from NodeWalker!')"}})
api("/execute", {"tool": "evaluate", "arguments": {"expression": "console.warn('This is a warning')"}})
api("/execute", {"tool": "evaluate", "arguments": {"expression": "console.error('This is an error')"}})
time.sleep(0.5)

# Read console logs
print("\n5. Get all console logs")
r = api("/execute", {"tool": "get_console_logs", "arguments": {}})
print(f"   Success: {r['success']}, Count: {r['result']['count']}")
for log in r['result']['logs']:
    print(f"   [{log['type']}] {log['text']}")

# Filter by level
print("\n6. Filter console logs by 'error' level")
r = api("/execute", {"tool": "get_console_logs", "arguments": {"level": "error"}})
print(f"   Error logs: {r['result']['count']}")
for log in r['result']['logs']:
    print(f"   [{log['type']}] {log['text']}")

# Filter network by method
print("\n7. Filter network logs by GET method")
r = api("/execute", {"tool": "get_network_logs", "arguments": {"method_filter": "GET"}})
print(f"   GET requests: {r['result']['count']}")

# Clear
print("\n8. Clear console & network logs")
r1 = api("/execute", {"tool": "clear_console_logs", "arguments": {}})
r2 = api("/execute", {"tool": "clear_network_logs", "arguments": {}})
print(f"   Console cleared: {r1['result']['cleared']}")
print(f"   Network cleared: {r2['result']['cleared']}")

# Verify cleared
r3 = api("/execute", {"tool": "get_console_logs", "arguments": {}})
r4 = api("/execute", {"tool": "get_network_logs", "arguments": {}})
print(f"   Console after clear: {r3['result']['count']}")
print(f"   Network after clear: {r4['result']['count']}")

print("\n" + "=" * 50)
print("All tests completed!")
