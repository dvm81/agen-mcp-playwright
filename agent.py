#!/usr/bin/env python3
"""
LLM Agent with Playwright MCP Server Integration

This agent:
1. Connects to the Microsoft Playwright MCP server
2. Gets available browser automation tools
3. Uses OpenAI GPT-4 to understand natural language commands
4. Executes multi-step workflows (navigate, search, download)
"""

import asyncio
import base64
from datetime import datetime
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in .env file")
    print("Please add your OpenAI API key to the .env file")
    sys.exit(1)


class PlaywrightAgent:
    """LLM Agent that uses Playwright MCP server for browser automation"""

    def __init__(self):
        self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
        self.mcp_session: ClientSession | None = None
        self.available_tools: List[Dict[str, Any]] = []
        self.conversation_history: List[Dict[str, Any]] = []
        self.downloads_dir = Path("downloads")
        self.downloads_dir.mkdir(exist_ok=True)

    def download_file(self, url: str, filename: str = None) -> str:
        """
        Download a file from a URL using Python requests.
        This is a custom tool that the LLM can use.

        Args:
            url: The URL of the file to download
            filename: Optional custom filename. If not provided, uses the name from URL

        Returns:
            Path to the downloaded file
        """
        try:
            # Get filename from URL if not provided
            if not filename:
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path)
                if not filename:
                    filename = "downloaded_file"

            filepath = self.downloads_dir / filename

            print(f"\n📥 Downloading from: {url}")
            print(f"   Saving as: {filename}")

            # Download the file
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Save to disk
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = os.path.getsize(filepath)
            print(f"✅ Downloaded successfully! Size: {file_size:,} bytes")
            print(f"   Location: {filepath}")

            return f"Successfully downloaded {filename} ({file_size:,} bytes) to {filepath}"

        except Exception as e:
            error_msg = f"Failed to download {url}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    async def save_screenshot(self, filename: str = None) -> str:
        """
        Take a screenshot and save it to the downloads folder.
        This wraps browser_take_screenshot and saves the result.

        Args:
            filename: Optional custom filename. If not provided, uses timestamp

        Returns:
            Path to the saved screenshot
        """
        try:
            # Generate filename with timestamp if not provided
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"
            elif not filename.endswith('.png'):
                filename = f"{filename}.png"

            filepath = self.downloads_dir / filename

            print(f"\n📸 Taking screenshot...")
            print(f"   Saving as: {filename}")

            # Call the MCP browser_take_screenshot tool
            result = await self.mcp_session.call_tool("browser_take_screenshot", {})

            # Extract base64 image data from result
            screenshot_data = None
            for content_item in result.content:
                if hasattr(content_item, 'data'):
                    screenshot_data = content_item.data
                    break

            if not screenshot_data:
                return "Error: No screenshot data returned from browser"

            # Decode base64 and save
            img_bytes = base64.b64decode(screenshot_data)

            with open(filepath, 'wb') as f:
                f.write(img_bytes)

            file_size = os.path.getsize(filepath)
            print(f"✅ Screenshot saved! Size: {file_size:,} bytes")
            print(f"   Location: {filepath}")

            return f"Successfully saved screenshot as {filename} ({file_size:,} bytes) to {filepath}"

        except Exception as e:
            error_msg = f"Failed to save screenshot: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    def convert_tools_for_openai(self) -> List[Dict[str, Any]]:
        """Convert MCP tools to OpenAI function calling format"""
        openai_tools = []

        # Add all MCP tools (browser automation)
        for tool in self.available_tools:
            openai_tool = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }
            }
            openai_tools.append(openai_tool)

        # Add our custom download_file tool
        openai_tools.append({
            "type": "function",
            "function": {
                "name": "download_file",
                "description": (
                    "Download a file (PDF, Excel, CSV, etc.) from a URL and save it to the downloads folder. "
                    "Use this after finding the file URL on a webpage. "
                    "Supports any file type: PDFs, Excel (.xlsx, .xls), CSV, images, etc."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The direct URL of the file to download (e.g., https://example.com/file.pdf)"
                        },
                        "filename": {
                            "type": "string",
                            "description": "Optional: Custom filename to save as. If not provided, uses the filename from the URL"
                        }
                    },
                    "required": ["url"]
                }
            }
        })

        # Add our custom save_screenshot tool
        openai_tools.append({
            "type": "function",
            "function": {
                "name": "save_screenshot",
                "description": (
                    "Take a screenshot of the current browser page and save it to the downloads folder as a PNG image. "
                    "Use this to capture the current state of a webpage."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Optional: Custom filename (without .png extension). If not provided, uses timestamp"
                        }
                    }
                }
            }
        })

        return openai_tools

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool (either MCP browser tool or custom download tool)"""
        print(f"\n🔧 Executing tool: {tool_name}")
        print(f"   Arguments: {json.dumps(arguments, indent=2)}")

        try:
            # Handle our custom download_file tool
            if tool_name == "download_file":
                return self.download_file(
                    url=arguments.get("url"),
                    filename=arguments.get("filename")
                )

            # Handle our custom save_screenshot tool
            if tool_name == "save_screenshot":
                return await self.save_screenshot(
                    filename=arguments.get("filename")
                )

            # Handle MCP tools (browser automation)
            result = await self.mcp_session.call_tool(tool_name, arguments)

            # Extract text content from result
            if result.content:
                response_text = ""
                for content_item in result.content:
                    if hasattr(content_item, 'text'):
                        response_text += content_item.text + "\n"

                print(f"✅ Tool result: {response_text.strip()}")
                return response_text.strip()

            return "Tool executed successfully (no content returned)"

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    async def process_user_message(self, user_message: str) -> str:
        """Process a user message and execute any needed tools"""
        print(f"\n💬 User: {user_message}")

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Prepare OpenAI tools
        openai_tools = self.convert_tools_for_openai()

        # Call OpenAI API with function calling
        max_iterations = 10  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get response from OpenAI
            response = self.openai_client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=self.conversation_history,
                tools=openai_tools,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Add assistant message to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls
            })

            # Check if the assistant wants to call tools
            if not assistant_message.tool_calls:
                # No more tools to call, return the final response
                final_response = assistant_message.content or "Done!"
                print(f"\n🤖 Assistant: {final_response}")
                return final_response

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                # Execute the tool via MCP
                tool_result = await self.execute_tool(function_name, function_args)

                # Add tool result to conversation history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                })

        return "Maximum iterations reached. Please try a simpler request."

    async def chat_loop(self):
        """Interactive chat loop for the agent"""
        print("\n" + "="*70)
        print("🤖 Playwright LLM Agent with Download Capability")
        print("="*70)
        print("\nExamples of what you can ask:")
        print("  - Navigate to https://www.irs.gov/forms-instructions")
        print("  - Find Form W-4 and download the PDF")
        print("  - Go to the IRS website and download Form 1040 PDF")
        print("  - Search for tax forms about retirement and download them")
        print("  - Take a screenshot of the current page")
        print(f"\n📁 Downloads will be saved to: {self.downloads_dir.absolute()}")
        print("\nType 'quit' or 'exit' to stop.")
        print("="*70 + "\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                # Process the message
                await self.process_user_message(user_input)

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


async def main():
    """Main entry point"""
    print("🔌 Connecting to Playwright MCP server...")

    # Configure server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    try:
        # Connect using context manager properly
        async with stdio_client(server_params) as (stdio, write):
            async with ClientSession(stdio, write) as session:
                await session.initialize()

                # Create and initialize agent
                agent = PlaywrightAgent()
                agent.mcp_session = session

                # Get available tools
                tools_response = await session.list_tools()

                print(f"✅ Connected! Found {len(tools_response.tools)} tools:")
                for tool in tools_response.tools:
                    print(f"  - {tool.name}: {tool.description[:60]}...")

                # Store tools
                agent.available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "input_schema": tool.inputSchema
                    }
                    for tool in tools_response.tools
                ]

                # Start interactive chat loop
                await agent.chat_loop()

    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
