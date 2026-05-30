"""
Basic Navigation Example

Demonstrates:
- Starting NodeWalker server connection
- Navigating to a URL
- Taking a screenshot
- Getting page text content
"""

import asyncio
import base64
from pathlib import Path
from nodewalker import BrowserController


async def main():
    """Navigate to a website and capture information."""

    # Connect to Chrome (must be running with --remote-debugging-port=9222)
    async with BrowserController(port=9222) as browser:
        print("✓ Connected to Chrome")

        # Navigate to a website
        print("\n→ Navigating to example.com...")
        result = await browser.navigate("https://example.com")
        print(f"✓ Loaded: {result['title']}")
        print(f"  URL: {result['url']}")

        # Get page text
        print("\n→ Extracting page text...")
        text_result = await browser.get_text()
        text = text_result['text']
        print(f"✓ Page text ({len(text)} chars):")
        print(f"  {text[:200]}...")

        # Take a screenshot
        print("\n→ Taking screenshot...")
        screenshot_result = await browser.screenshot(format="png")

        # Save screenshot to file
        screenshot_data = screenshot_result['data']
        screenshot_bytes = base64.b64decode(screenshot_data)

        output_path = Path(__file__).parent / "screenshot_example.png"
        output_path.write_bytes(screenshot_bytes)

        print(f"✓ Screenshot saved: {output_path}")
        print(f"  Size: {screenshot_result['size_kb']:.1f} KB")

        print("\n✓ Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("NodeWalker - Basic Navigation Example")
    print("=" * 60)
    print("\nMake sure Chrome is running with:")
    print("  chrome --remote-debugging-port=9222")
    print()

    asyncio.run(main())
