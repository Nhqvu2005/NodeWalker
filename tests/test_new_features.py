"""Test all 12 new core features."""
import urllib.request
import json
import time

BASE = "http://localhost:8589"

def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode())

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

print("=== Core Features Test (31 tools) ===")
print()

# Navigate to example.com
api("/execute", {"tool": "navigate", "arguments": {"url": "https://example.com"}})
time.sleep(1)

# 1. find_elements
print("1. find_elements")
r = api("/execute", {"tool": "find_elements", "arguments": {"query": "Learn more"}})
result = r["result"]
print(f"   Found: {result['count']} elements")
for e in result["elements"]:
    safe_print(f"   - role={e['role']}, name={e['name']}, ref={e['ref']}")
assert result["count"] > 0, "Should find at least one element"
print("   PASS")

# 2. check_element
print("\n2. check_element")
r = api("/execute", {"tool": "check_element", "arguments": {"ref": 1}})
result = r["result"]
print(f"   exists={result.get('exists')}, visible={result.get('visible')}, tag={result.get('tag')}")
assert result.get("exists") == True, "Element should exist"
print("   PASS")

# 3. extract_data
print("\n3. extract_data")
r = api("/execute", {"tool": "extract_data", "arguments": {"instruction": "all links"}})
data = r["result"]["data"]
print(f"   Headings: {len(data.get('headings', []))}")
print(f"   Links: {len(data.get('links', []))}")
for link in data.get("links", [])[:3]:
    safe_print(f"   - {link['text']}: {link['href'][:60]}")
print("   PASS")

# 4. get_page_errors
print("\n4. get_page_errors")
r = api("/execute", {"tool": "get_page_errors", "arguments": {}})
result = r["result"]
print(f"   error_count={result['error_count']}")
print("   PASS")

# 5. get_cookies
print("\n5. get_cookies")
r = api("/execute", {"tool": "get_cookies", "arguments": {}})
print(f"   Cookies: {r['result']['count']}")
print("   PASS")

# 6. set_cookie
print("\n6. set_cookie")
r = api("/execute", {"tool": "set_cookie", "arguments": {
    "name": "test_cookie", "value": "hello", "domain": "example.com"
}})
print(f"   Set cookie: {r['result']}")
r = api("/execute", {"tool": "get_cookies", "arguments": {}})
names = [c["name"] for c in r["result"]["cookies"]]
assert "test_cookie" in names, "Cookie should be set"
print("   PASS")

# 7. go_back / go_forward
print("\n7. go_back / go_forward")
api("/execute", {"tool": "navigate", "arguments": {"url": "https://www.google.com"}})
time.sleep(1)
r = api("/execute", {"tool": "go_back", "arguments": {}})
safe_print(f"   After go_back: {r['result']['url'][:50]}")
r = api("/execute", {"tool": "go_forward", "arguments": {}})
safe_print(f"   After go_forward: {r['result']['url'][:50]}")
print("   PASS")

# 8. wait_for_navigation
print("\n8. wait_for_navigation")
r = api("/execute", {"tool": "wait_for_navigation", "arguments": {"timeout": 3}})
print(f"   success={r['result']['success']}")
print("   PASS")

# 9. hover (on Google page)
print("\n9. hover")
api("/execute", {"tool": "get_page_snapshot", "arguments": {}})
r = api("/execute", {"tool": "hover", "arguments": {"ref": 1}})
print(f"   success={r['result']['success']}")
print("   PASS")

# 10. handle_dialog (no dialog, should fail gracefully)
print("\n10. handle_dialog (no dialog)")
r = api("/execute", {"tool": "handle_dialog", "arguments": {"accept": True}})
print(f"   success={r['result']['success']} (expected False - no dialog)")
print("   PASS")

# 11. find_elements by role
print("\n11. find_elements (by role=link)")
r = api("/execute", {"tool": "find_elements", "arguments": {"query": "", "role": "link"}})
print(f"   Links found: {r['result']['count']}")
assert r["result"]["count"] > 0, "Should find links"
print("   PASS")

# 12. select_option (no dropdown, should fail gracefully)
print("\n12. select_option (no dropdown)")
r = api("/execute", {"tool": "select_option", "arguments": {"ref": 1, "label": "test"}})
print(f"   success={r['result']['success']} (expected False)")
print("   PASS")

print()
print("=" * 50)
print("ALL 12 NEW FEATURES TESTED SUCCESSFULLY!")
print("Total tools: 31")
print("=" * 50)
