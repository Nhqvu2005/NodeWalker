"""
Form Filling Example

Demonstrates:
- Finding and filling input fields
- Clicking buttons
- Waiting for elements
- Handling form submission
"""

import asyncio
from nodewalker import BrowserController


async def main():
    """Automate a login form."""

    async with BrowserController(port=9222) as browser:
        print("✓ Connected to Chrome")

        # Navigate to a demo login page
        print("\n→ Navigating to demo login page...")
        await browser.navigate("https://the-internet.herokuapp.com/login")
        print("✓ Page loaded")

        # Fill username field
        print("\n→ Filling username...")
        await browser.type_text(
            selector="#username",
            text="tomsmith",
            clear_first=True
        )
        print("✓ Username entered")

        # Fill password field
        print("\n→ Filling password...")
        await browser.type_text(
            selector="#password",
            text="SuperSecretPassword!",
            clear_first=True
        )
        print("✓ Password entered")

        # Click login button
        print("\n→ Clicking login button...")
        await browser.click("button[type='submit']")
        print("✓ Login button clicked")

        # Wait for success message
        print("\n→ Waiting for success message...")
        await browser.wait_for("#flash", timeout=5)

        # Get the flash message
        flash_result = await browser.get_text(selector="#flash")
        flash_text = flash_result['text'].strip()
        print(f"✓ Flash message: {flash_text}")

        # Verify we're logged in
        current_url = (await browser.evaluate("window.location.href"))['result']
        if "/secure" in current_url:
            print("\n✓ Successfully logged in!")
            print(f"  Current URL: {current_url}")
        else:
            print("\n✗ Login failed")

        print("\n✓ Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("NodeWalker - Form Filling Example")
    print("=" * 60)
    print("\nMake sure Chrome is running with:")
    print("  chrome --remote-debugging-port=9222")
    print()

    asyncio.run(main())
