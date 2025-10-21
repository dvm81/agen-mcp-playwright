#!/usr/bin/env python3
"""
Advanced Demo: Search for a form and download the PDF
Shows multi-step workflow with the LLM agent
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


async def demo_search_and_download():
    print("="*70)
    print("🎬 Advanced Demo: Search + Download Workflow")
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

            # Multi-step user command
            user_command = """
            Go to the IRS forms website at https://www.irs.gov/forms-instructions
            and then click on the link to download Form W-4 PDF.
            """

            print(f"\n💬 User: {user_command.strip()}")

            # Conversation history
            messages = [
                {"role": "user", "content": user_command}
            ]

            # Multi-step loop
            max_iterations = 10
            iteration = 0

            print("\n🔄 Starting multi-step workflow...\n")

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

                # Add assistant message to history
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": assistant_message.tool_calls
                })

                # Check if GPT wants to call tools
                if not assistant_message.tool_calls:
                    # No more tools, task complete
                    final_response = assistant_message.content or "Done!"
                    print(f"\n🤖 Assistant: {final_response}")
                    break

                # Execute each tool call
                for tool_call in assistant_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    print(f"\n🔧 Tool: {function_name}")
                    print(f"   Args: {json.dumps(function_args, indent=2)}")

                    # Execute via MCP
                    result = await session.call_tool(function_name, function_args)

                    # Extract result text
                    result_text = ""
                    for content_item in result.content:
                        if hasattr(content_item, 'text'):
                            result_text += content_item.text

                    # Show abbreviated result
                    if len(result_text) > 500:
                        print(f"   ✅ Result: {result_text[:500]}... (truncated)")
                    else:
                        print(f"   ✅ Result: {result_text}")

                    # Add tool result to conversation
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result_text
                    })

                print()  # Newline between iterations

            print("\n" + "="*70)
            print("🎉 Demo complete!")
            print("="*70)

            # Keep browser open briefly
            print("\n⏸️  Keeping browser open for 10 seconds...")
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(demo_search_and_download())
