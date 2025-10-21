#!/usr/bin/env python3
"""
Demo script to show the agent in action
This simulates the user typing commands
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


async def demo():
    print("="*70)
    print("🎬 LLM Agent Demo - Browser Automation with Natural Language")
    print("="*70)

    # Configure and connect to Playwright MCP server
    print("\n🔌 Connecting to Playwright MCP server...")
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            # Get tools
            tools_response = await session.list_tools()
            print(f"✅ Connected! Found {len(tools_response.tools)} tools")

            # Convert to OpenAI format
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

            # Initialize OpenAI client
            openai_client = OpenAI(api_key=OPENAI_API_KEY)

            # Demo command
            user_command = "Navigate to https://www.irs.gov/forms-instructions"
            print(f"\n💬 User: {user_command}")

            # Send to GPT
            messages = [
                {"role": "user", "content": user_command}
            ]

            print("\n🤖 Calling GPT-4o to decide which tools to use...")
            response = openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            if assistant_message.tool_calls:
                print(f"\n✅ GPT decided to use {len(assistant_message.tool_calls)} tool(s):")

                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"\n🔧 Tool: {function_name}")
                    print(f"   Arguments: {json.dumps(function_args, indent=2)}")

                    # Execute the tool
                    print(f"\n⏳ Executing {function_name}...")
                    result = await session.call_tool(function_name, function_args)

                    # Extract result
                    result_text = ""
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            result_text += content_item.text

                    print(f"✅ Result: {result_text}")

                print("\n" + "="*70)
                print("🎉 Demo complete! The browser should now be on the IRS forms page.")
                print("="*70)
            else:
                print(f"\n🤖 Assistant: {assistant_message.content}")

            # Keep browser open for a bit so you can see it
            print("\n⏸️  Keeping browser open for 10 seconds so you can see it...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(demo())
