#!/usr/bin/env python3
"""
Full Download Demo: Search, Find URL, and Download Files

This demonstrates the complete workflow:
1. Navigate to IRS forms page
2. Find Form W-4 link
3. Extract the PDF URL
4. Download the PDF to disk using our custom tool
"""

import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def download_file(url: str, filename: str = None) -> str:
    """Download a file using Python requests"""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    if not filename:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

    filepath = downloads_dir / filename

    print(f"\n📥 Downloading from: {url}")
    print(f"   Saving as: {filename}")

    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size = os.path.getsize(filepath)
    print(f"✅ Downloaded successfully! Size: {file_size:,} bytes")
    print(f"   Location: {filepath.absolute()}")

    return f"Successfully downloaded {filename} ({file_size:,} bytes) to {filepath}"


async def demo_full_workflow():
    print("="*70)
    print("🎬 Full Download Workflow Demo")
    print("="*70)
    print("\nThis demo will:")
    print("  1. Navigate to IRS forms page")
    print("  2. Use the LLM to find Form W-4 PDF URL")
    print("  3. Download the PDF to downloads/ folder")
    print("="*70)

    # Connect to Playwright MCP server
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

            # Convert MCP tools to OpenAI format
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

            # Add our custom download_file tool
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": "download_file",
                    "description": (
                        "Download a file (PDF, Excel, CSV, etc.) from a URL and save it to the downloads folder. "
                        "Use this after finding the file URL on a webpage."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The direct URL of the file to download"
                            },
                            "filename": {
                                "type": "string",
                                "description": "Optional: Custom filename"
                            }
                        },
                        "required": ["url"]
                    }
                }
            })

            print(f"✅ Total tools available (including download_file): {len(openai_tools)}")

            # Initialize OpenAI
            openai_client = OpenAI(api_key=OPENAI_API_KEY)

            # User request
            user_request = """
            Go to https://www.irs.gov/forms-instructions and find the direct URL
            for Form W-4 PDF, then download it using the download_file tool.
            """

            print(f"\n💬 User: {user_request.strip()}")

            messages = [{"role": "user", "content": user_request}]

            # Multi-step loop
            max_iterations = 10
            iteration = 0

            print("\n🔄 Starting workflow...\n")

            while iteration < max_iterations:
                iteration += 1
                print(f"--- Iteration {iteration} ---")

                # Call GPT
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=messages,
                    tools=openai_tools,
                    tool_choice="auto"
                )

                assistant_message = response.choices[0].message

                # Add to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })

                # Check if done
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

                    # Execute
                    if function_name == "download_file":
                        # Use our Python download function
                        result_text = download_file(
                            url=function_args.get("url"),
                            filename=function_args.get("filename")
                        )
                    else:
                        # Use MCP tools
                        result = await session.call_tool(function_name, function_args)
                        result_text = ""
                        for content_item in result.content:
                            if hasattr(content_item, 'text'):
                                result_text += content_item.text

                        # Show abbreviated result
                        if len(result_text) > 300:
                            print(f"   ✅ Result: {result_text[:300]}... (truncated)")
                        else:
                            print(f"   ✅ Result: {result_text}")

                    # Add to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })

                print()

            print("\n" + "="*70)
            print("🎉 Demo Complete!")
            print("="*70)
            print("\n📂 Check the downloads/ folder for your files!")
            print()

            # List downloaded files
            downloads_dir = Path("downloads")
            if downloads_dir.exists():
                files = list(downloads_dir.glob("*"))
                if files:
                    print("Downloaded files:")
                    for f in files:
                        size = f.stat().st_size
                        print(f"  - {f.name} ({size:,} bytes)")

            print("\n⏸️  Keeping browser open for 5 seconds...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(demo_full_workflow())
