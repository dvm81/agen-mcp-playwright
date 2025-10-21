#!/usr/bin/env python3
"""Test how browser_take_screenshot works"""

import asyncio
import base64
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_screenshot():
    print("Testing browser_take_screenshot tool...\n")

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            # Navigate to a page first
            print("1. Navigating to example.com...")
            await session.call_tool("browser_navigate", {"url": "https://example.com"})
            print("   ✅ Navigated\n")

            # Take screenshot
            print("2. Taking screenshot...")
            result = await session.call_tool("browser_take_screenshot", {})

            # Examine the result
            print("3. Screenshot result:")
            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    text = content_item.text[:500]
                    print(f"   Text: {text}...")
                if hasattr(content_item, 'data'):
                    print(f"   Has data attribute!")
                    print(f"   Data type: {type(content_item.data)}")
                    print(f"   Data length: {len(content_item.data) if hasattr(content_item.data, '__len__') else 'N/A'}")

                # Check all attributes
                print(f"   All attributes: {dir(content_item)}")

            # Try to save if we got base64 data
            for content_item in result.content:
                if hasattr(content_item, 'data'):
                    # Assume it's base64
                    try:
                        img_data = base64.b64decode(content_item.data)
                        downloads_dir = Path("downloads")
                        downloads_dir.mkdir(exist_ok=True)

                        filepath = downloads_dir / "test_screenshot.png"
                        with open(filepath, 'wb') as f:
                            f.write(img_data)

                        print(f"\n✅ Saved screenshot to {filepath}")
                        print(f"   Size: {len(img_data):,} bytes")
                    except Exception as e:
                        print(f"   Error saving: {e}")


if __name__ == "__main__":
    asyncio.run(test_screenshot())
