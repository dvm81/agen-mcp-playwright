#!/usr/bin/env python3
"""Simple test to verify MCP connection to Playwright server"""

import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_connection():
    print("🧪 Testing MCP connection to Playwright server...")

    try:
        # Configure server
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@playwright/mcp@latest"],
            env=None
        )

        print("📡 Launching Playwright MCP server...")

        # Connect using context manager properly
        async with stdio_client(server_params) as (stdio, write):
            # Initialize session
            async with ClientSession(stdio, write) as session:
                await session.initialize()

                print("✅ MCP session initialized!")

                # Get available tools
                tools_response = await session.list_tools()

                print(f"\n📦 Found {len(tools_response.tools)} tools:")
                for i, tool in enumerate(tools_response.tools, 1):
                    print(f"  {i}. {tool.name}")
                    print(f"     {tool.description[:80]}...")

                print("\n✅ Connection test successful!")
                return True

    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
