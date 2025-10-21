#!/usr/bin/env python3
"""
Screenshot Demo: Navigate and take screenshots

This demonstrates:
1. Navigate to IRS forms page
2. Take a screenshot and save it to downloads folder
3. LLM automatically uses save_screenshot tool
"""

import asyncio
import base64
from datetime import datetime
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


async def save_screenshot(session, filename: str = None) -> str:
    """Helper to save screenshot"""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
    elif not filename.endswith('.png'):
        filename = f"{filename}.png"

    filepath = downloads_dir / filename

    print(f"\n📸 Taking screenshot...")
    result = await session.call_tool("browser_take_screenshot", {})

    for content_item in result.content:
        if hasattr(content_item, 'data'):
            img_bytes = base64.b64decode(content_item.data)
            with open(filepath, 'wb') as f:
                f.write(img_bytes)

            file_size = os.path.getsize(filepath)
            print(f"✅ Screenshot saved! Size: {file_size:,} bytes")
            print(f"   Location: {filepath}")
            return f"Successfully saved screenshot as {filename} ({file_size:,} bytes)"

    return "Error: No screenshot data"


async def demo_screenshot():
    print("="*70)
    print("📸 Screenshot Demo with LLM")
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
            tools_response = await session.list_tools()
            print(f"✅ Connected! Found {len(tools_response.tools)} browser tools")

            # Convert tools
            openai_tools = []
            for tool in tools_response.tools:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })

            # Add custom save_screenshot tool
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": "save_screenshot",
                    "description": "Take a screenshot and save it to downloads folder as PNG",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Optional filename (without .png)"
                            }
                        }
                    }
                }
            })

            print(f"✅ Total tools (including save_screenshot): {len(openai_tools)}")

            # Initialize OpenAI
            openai_client = OpenAI(api_key=OPENAI_API_KEY)

            # User request
            user_request = """
            Navigate to https://www.irs.gov/forms-instructions and then
            take a screenshot and save it as 'irs_forms_page'.
            """

            print(f"\n💬 User: {user_request.strip()}")

            messages = [{"role": "user", "content": user_request}]

            # Multi-step loop
            max_iterations = 5
            iteration = 0

            print("\n🔄 Starting workflow...\n")

            while iteration < max_iterations:
                iteration += 1
                print(f"--- Iteration {iteration} ---")

                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                assistant_message = response.choices[0].message

                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })

                if not assistant_message.tool_calls:
                    final_response = assistant_message.content or "Done!"
                    print(f"\n🤖 Assistant: {final_response}")
                    break

                # Execute tools
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"\n🔧 Tool: {function_name}")
                    print(f"   Args: {json.dumps(function_args, indent=2)}")

                    if function_name == "save_screenshot":
                        result_text = await save_screenshot(
                            session,
                            filename=function_args.get("filename")
                        )
                    else:
                        result = await session.call_tool(function_name, function_args)
                        result_text = ""
                        for content_item in result.content:
                            if hasattr(content_item, 'text'):
                                result_text += content_item.text

                        if len(result_text) > 300:
                            print(f"   ✅ Result: {result_text[:300]}... (truncated)")
                        else:
                            print(f"   ✅ Result: {result_text}")

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })

                print()

            print("\n" + "="*70)
            print("🎉 Demo Complete!")
            print("="*70)

            # List screenshots
            downloads_dir = Path("downloads")
            screenshots = list(downloads_dir.glob("*.png"))
            if screenshots:
                print("\n📸 Screenshots in downloads folder:")
                for f in screenshots:
                    size = f.stat().st_size
                    print(f"  - {f.name} ({size:,} bytes)")

            print("\n⏸️  Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(demo_screenshot())
