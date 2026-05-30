"""
Web Scraping Example

Demonstrates:
- Navigating to multiple pages
- Extracting structured data
- Using JavaScript evaluation
- Scrolling and pagination
"""

import asyncio
import json
from nodewalker import BrowserController


async def scrape_quotes(browser: BrowserController, max_pages: int = 3):
    """Scrape quotes from quotes.toscrape.com"""

    all_quotes = []
    base_url = "https://quotes.toscrape.com"

    for page_num in range(1, max_pages + 1):
        url = f"{base_url}/page/{page_num}/"
        print(f"\n→ Scraping page {page_num}...")

        await browser.navigate(url)

        # Extract quotes using JavaScript
        js_code = """
        Array.from(document.querySelectorAll('.quote')).map(quote => ({
            text: quote.querySelector('.text').innerText,
            author: quote.querySelector('.author').innerText,
            tags: Array.from(quote.querySelectorAll('.tag')).map(tag => tag.innerText)
        }))
        """

        result = await browser.evaluate(js_code)
        quotes = result['result']

        print(f"✓ Found {len(quotes)} quotes on page {page_num}")
        all_quotes.extend(quotes)

        # Check if there's a next page
        next_button = await browser.evaluate(
            "document.querySelector('.next') !== null"
        )

        if not next_button['result']:
            print("✓ Reached last page")
            break

    return all_quotes


async def main():
    """Scrape quotes and save to JSON."""

    async with BrowserController(port=9222) as browser:
        print("✓ Connected to Chrome")

        # Scrape quotes
        quotes = await scrape_quotes(browser, max_pages=3)

        print(f"\n✓ Total quotes scraped: {len(quotes)}")

        # Display first 3 quotes
        print("\n📝 Sample quotes:")
        for i, quote in enumerate(quotes[:3], 1):
            print(f"\n{i}. \"{quote['text']}\"")
            print(f"   — {quote['author']}")
            print(f"   Tags: {', '.join(quote['tags'])}")

        # Save to JSON file
        output_file = "scraped_quotes.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Saved {len(quotes)} quotes to {output_file}")
        print("\n✓ Done!")


if __name__ == "__main__":
    print("=" * 60)
    print("NodeWalker - Web Scraping Example")
    print("=" * 60)
    print("\nMake sure Chrome is running with:")
    print("  chrome --remote-debugging-port=9222")
    print()

    asyncio.run(main())
