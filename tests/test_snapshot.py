"""Test accessibility tree snapshot & ref-based interaction."""
import urllib.request
import json
import time
import sys

BASE = "http://localhost:8588"

def safe_print(text):
    """Print with fallback for Windows encoding issues."""
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

print("Accessibility Tree Snapshot Test")
print("=" * 60)

# 1. Check tool count (should be 19)
tools = api("/tools")
names = [t["function"]["name"] for t in tools]
print(f"\n1. Tool count: {len(tools)} (expected 19)")
assert "get_page_snapshot" in names, "get_page_snapshot missing!"
assert "click_ref" in names, "click_ref missing!"
assert "type_ref" in names, "type_ref missing!"
print("   New tools present: get_page_snapshot, click_ref, type_ref")

# 2. Navigate to a page
print("\n2. Navigate to example.com")
r = api("/execute", {"tool": "navigate", "arguments": {"url": "https://example.com"}})
print(f"   Success: {r['success']}")
time.sleep(1)

# 3. Get page snapshot — THE KEY TEST
print("\n3. Get page snapshot (accessibility tree)")
r = api("/execute", {"tool": "get_page_snapshot", "arguments": {}})
result = r["result"]
print(f"   Success: {result['success']}")
print(f"   Title: {result.get('title', 'N/A')}")
print(f"   URL: {result.get('url', 'N/A')}")
print(f"   Ref count: {result.get('ref_count', 0)}")
print(f"\n   --- Snapshot ---")
snapshot = result.get("snapshot", "")
safe_print(snapshot)
print(f"   --- End ({len(snapshot)} chars) ---")

# 4. Compare token efficiency
print("\n4. Token efficiency comparison")
r_text = api("/execute", {"tool": "get_text", "arguments": {}})
text_len = len(r_text.get("result", {}).get("text", ""))
r_html = api("/execute", {"tool": "get_html", "arguments": {}})
html_len = len(r_html.get("result", {}).get("html", ""))
snap_len = len(snapshot)
print(f"   get_html:          {html_len:>6} chars")
print(f"   get_text:          {text_len:>6} chars")
print(f"   get_page_snapshot: {snap_len:>6} chars")
if html_len > 0:
    reduction = round((1 - snap_len / html_len) * 100)
    print(f"   Token reduction vs HTML: ~{reduction}%")

# 5. Test click_ref (click the "More information..." link)
print("\n5. Test click_ref")
if result.get("ref_count", 0) > 0:
    ref_to_click = 1
    print(f"   Clicking ref={ref_to_click}")
    r = api("/execute", {"tool": "click_ref", "arguments": {"ref": ref_to_click}})
    click_result = r.get("result", {})
    print(f"   Success: {click_result.get('success')}")
    print(f"   Clicked: {click_result.get('clicked', {})}")
    time.sleep(1)
    
    r2 = api("/execute", {"tool": "get_page_snapshot", "arguments": {}})
    new_title = r2.get("result", {}).get("title", "")
    new_url = r2.get("result", {}).get("url", "")
    safe_print(f"   New page title: {new_title}")
    safe_print(f"   New page URL: {new_url}")
else:
    print("   No refs found, skipping click test")

# 6. Navigate to Google and test type_ref
print("\n6. Navigate to Google for type_ref test")
api("/execute", {"tool": "navigate", "arguments": {"url": "https://www.google.com"}})
time.sleep(1)

r = api("/execute", {"tool": "get_page_snapshot", "arguments": {}})
snap_result = r.get("result", {})
print(f"   Google snapshot ref_count: {snap_result.get('ref_count', 0)}")
google_snap = snap_result.get("snapshot", "")
lines = google_snap.split("\n")
for line in lines[:30]:
    safe_print(f"   {line}")
if len(lines) > 30:
    print(f"   ... ({len(lines) - 30} more lines)")

# Find a textbox ref for typing
print("\n   Looking for textbox ref...")
for line in lines:
    if "textbox" in line.lower() or "searchbox" in line.lower():
        print(f"   Found: {line.strip()}")
        # Extract ref number
        import re
        ref_match = re.search(r'\[ref=(\d+)\]', line)
        if ref_match:
            text_ref = int(ref_match.group(1))
            print(f"   Typing into ref={text_ref}")
            r = api("/execute", {"tool": "type_ref", "arguments": {"ref": text_ref, "text": "NodeWalker test"}})
            type_result = r.get("result", {})
            print(f"   Type success: {type_result.get('success')}")
            print(f"   Typed: {type_result.get('typed', '')}")
        break

# 7. Test invalid ref
print("\n7. Test invalid ref (should fail gracefully)")
r = api("/execute", {"tool": "click_ref", "arguments": {"ref": 99999}})
print(f"   Result: {r.get('result', {})}")

print("\n" + "=" * 60)
print("All snapshot tests completed!")
