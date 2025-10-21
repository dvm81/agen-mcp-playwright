#!/usr/bin/env python3
"""
Demo: Actually downloading files using browser_evaluate

This shows how to download a file by:
1. Navigate to the page
2. Use JavaScript to fetch the file
3. Save it using browser_evaluate
"""

import asyncio
import json
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


async def demo_actual_download():
    print("="*70)
    print("🎬 Demo: Actual File Download Using JavaScript")
    print("="*70)

    print("\n🔌 Connecting to Playwright MCP server...")
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()
            print("✅ Connected!")

            # Step 1: Navigate to IRS forms page
            print("\n📍 Step 1: Navigate to IRS forms page")
            result = await session.call_tool(
                "browser_navigate",
                {"url": "https://www.irs.gov/forms-instructions"}
            )
            print("✅ Navigated successfully")

            # Step 2: Use JavaScript to download Form W-4 PDF
            print("\n📥 Step 2: Download Form W-4 PDF using JavaScript")

            download_js = """
            (async () => {
                const url = 'https://www.irs.gov/pub/irs-pdf/fw4.pdf';
                const response = await fetch(url);
                const blob = await response.blob();
                const arrayBuffer = await blob.arrayBuffer();
                const bytes = new Uint8Array(arrayBuffer);

                // Convert to base64 for transmission
                let binary = '';
                for (let i = 0; i < bytes.byteLength; i++) {
                    binary += String.fromCharCode(bytes[i]);
                }
                const base64 = btoa(binary);

                return {
                    filename: 'fw4.pdf',
                    size: bytes.length,
                    base64: base64.substring(0, 100) + '... (truncated)',
                    success: true
                };
            })()
            """

            result = await session.call_tool(
                "browser_evaluate",
                {"expression": download_js}
            )

            for content_item in result.content:
                if hasattr(content_item, 'text'):
                    print(f"✅ Result: {content_item.text[:500]}")

            print("\n" + "="*70)
            print("📌 NOTE: The Playwright MCP server doesn't directly save files.")
            print("   The browser can navigate to PDFs but won't save them to disk.")
            print("   We demonstrated fetching the file with JavaScript.")
            print("="*70)

            print("\n⏸️  Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(demo_actual_download())
