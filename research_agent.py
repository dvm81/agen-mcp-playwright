#!/usr/bin/env python3
"""
Research Agent - LangGraph-powered website exploration

This module uses LangGraph to create a state machine that:
1. Takes an exploration plan from the scoper
2. Visits each page systematically
3. Extracts content using web_extractor
4. Downloads relevant files
5. Takes screenshots
6. Synthesizes findings
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict, List, Dict, Any, Annotated

from dotenv import load_dotenv
from mcp import ClientSession
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from web_extractor import WebContentExtractor

load_dotenv()


# Define the state for our research workflow
class ResearchState(TypedDict):
    """State maintained throughout the research process"""
    # Input
    exploration_plan: Dict[str, Any]

    # Progress tracking
    current_page_index: int
    visited_urls: List[str]

    # Collected data
    page_contents: List[Dict[str, Any]]  # {url, title, content, timestamp}
    downloads: List[str]  # Downloaded file paths
    screenshots: List[str]  # Screenshot paths

    # LLM communication
    messages: Annotated[list, add_messages]

    # Control
    should_continue: bool
    research_complete: bool


class ResearchAgent:
    """LangGraph-powered research agent"""

    def __init__(self, mcp_session: ClientSession, llm_model: str = "gpt-4o"):
        self.session = mcp_session
        self.llm = ChatOpenAI(model=llm_model, temperature=0)
        self.extractor = WebContentExtractor(mcp_session)

        # Create output directory
        self.output_dir = Path("research_outputs")
        self.output_dir.mkdir(exist_ok=True)

        # Build the LangGraph workflow
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph state machine"""

        # Create the graph
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("navigate", self._navigate_node)
        workflow.add_node("extract", self._extract_node)
        workflow.add_node("collect", self._collect_node)
        workflow.add_node("synthesize", self._synthesize_node)

        # Define the flow
        workflow.set_entry_point("navigate")

        workflow.add_edge("navigate", "extract")
        workflow.add_edge("extract", "collect")
        workflow.add_edge("collect", "synthesize")

        # After synthesize, decide whether to continue or end
        workflow.add_conditional_edges(
            "synthesize",
            self._should_continue,
            {
                "continue": "navigate",
                "end": END
            }
        )

        return workflow.compile()

    async def _navigate_node(self, state: ResearchState) -> ResearchState:
        """Navigate to the next page in the plan"""
        plan = state["exploration_plan"]
        pages = plan["pages_to_explore"]
        current_idx = state["current_page_index"]

        if current_idx >= len(pages):
            state["research_complete"] = True
            return state

        page_info = pages[current_idx]
        url = page_info["url"]

        print(f"\n{'='*70}")
        print(f"📍 Navigating to page {current_idx + 1}/{len(pages)}")
        print(f"   URL: {url}")
        print(f"   Priority: {page_info['priority']}")
        print(f"   Reason: {page_info['reason']}")
        print(f"{'='*70}")

        # Navigate using Playwright
        try:
            await self.session.call_tool("browser_navigate", {"url": url})
            state["visited_urls"].append(url)
            print(f"✅ Navigation successful")
        except Exception as e:
            print(f"❌ Navigation failed: {e}")
            # Skip this page
            state["current_page_index"] += 1

        return state

    async def _extract_node(self, state: ResearchState) -> ResearchState:
        """Extract content from the current page"""
        plan = state["exploration_plan"]
        pages = plan["pages_to_explore"]
        current_idx = state["current_page_index"]

        if current_idx >= len(pages):
            return state

        page_info = pages[current_idx]
        url = page_info["url"]

        print(f"\n📄 Extracting content from current page...")

        try:
            # Use our web extractor
            content_data = await self.extractor.extract_content(url)

            # Add metadata
            content_data["priority"] = page_info["priority"]
            content_data["reason"] = page_info["reason"]
            content_data["timestamp"] = datetime.now().isoformat()

            # Store the content
            state["page_contents"].append(content_data)

            print(f"✅ Extracted {content_data['length']} characters")
            print(f"   Title: {content_data['title']}")
            print(f"   Method: {content_data['method']}")

        except Exception as e:
            print(f"❌ Extraction failed: {e}")

        return state

    async def _collect_node(self, state: ResearchState) -> ResearchState:
        """Collect additional resources (screenshots, downloads)"""
        plan = state["exploration_plan"]
        pages = plan["pages_to_explore"]
        current_idx = state["current_page_index"]

        if current_idx >= len(pages):
            return state

        page_info = pages[current_idx]
        url = page_info["url"]

        print(f"\n📸 Collecting resources...")

        # Take screenshot if high priority
        if page_info["priority"] == "high":
            try:
                # Generate filename from URL
                filename = self._url_to_filename(url)
                screenshot_path = f"research_{filename}"

                # Use our existing screenshot capability
                screenshot_js = """
                (() => {
                    return document.documentElement.outerHTML.length;
                })()
                """

                # Take screenshot via MCP
                result = await self.session.call_tool("browser_take_screenshot", {})

                # Save screenshot data
                import base64
                for item in result.content:
                    if hasattr(item, 'data'):
                        img_data = base64.b64decode(item.data)
                        filepath = self.output_dir / f"{screenshot_path}.png"
                        with open(filepath, 'wb') as f:
                            f.write(img_data)

                        state["screenshots"].append(str(filepath))
                        print(f"   📸 Screenshot saved: {filepath.name}")
                        break

            except Exception as e:
                print(f"   ⚠️  Screenshot failed: {e}")

        # Look for downloadable files (PDFs, etc.)
        # This is a simplified version - you can enhance it
        try:
            find_pdfs_js = """
            (() => {
                const pdfs = Array.from(document.querySelectorAll('a[href$=".pdf"]'))
                    .slice(0, 3)
                    .map(a => ({
                        text: a.innerText.trim(),
                        url: a.href
                    }));
                return pdfs;
            })()
            """

            # This would extract PDF links - simplified for now
            # In a full implementation, you'd download these

        except Exception as e:
            pass

        return state

    async def _synthesize_node(self, state: ResearchState) -> ResearchState:
        """Synthesize findings from current page"""
        plan = state["exploration_plan"]
        pages = plan["pages_to_explore"]
        current_idx = state["current_page_index"]

        if current_idx >= len(pages):
            return state

        page_contents = state["page_contents"]
        if not page_contents or current_idx >= len(page_contents):
            state["current_page_index"] += 1
            return state

        current_content = page_contents[current_idx]

        print(f"\n🤖 Synthesizing findings...")

        # Use LLM to extract key findings
        synthesis_prompt = f"""Extract the key findings from this webpage content related to the research topic.

Research Topic: {plan['topic']}
Page URL: {current_content['url']}
Page Title: {current_content['title']}

Content:
{current_content['content'][:3000]}  # Limit to 3000 chars for LLM

Please provide:
1. 3-5 key points relevant to the research topic
2. Any important quotes or facts
3. Whether this page contains valuable information (yes/no/somewhat)

Return as JSON:
{{
    "key_points": ["point 1", "point 2", ...],
    "quotes": ["quote 1", ...],
    "value": "yes|no|somewhat",
    "summary": "1-2 sentence summary"
}}
"""

        try:
            messages = [HumanMessage(content=synthesis_prompt)]
            response = self.llm.invoke(messages)

            # Parse response
            response_text = response.content
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            synthesis = json.loads(json_str)

            # Add synthesis to content
            current_content["synthesis"] = synthesis

            print(f"✅ Synthesis complete")
            print(f"   Value: {synthesis.get('value', 'unknown')}")
            print(f"   Key points: {len(synthesis.get('key_points', []))}")

        except Exception as e:
            print(f"⚠️  Synthesis failed: {e}")
            current_content["synthesis"] = {
                "key_points": [],
                "value": "unknown",
                "summary": "Synthesis failed"
            }

        # Move to next page
        state["current_page_index"] += 1

        return state

    def _should_continue(self, state: ResearchState) -> str:
        """Decide whether to continue exploring or end"""
        plan = state["exploration_plan"]
        pages = plan["pages_to_explore"]
        current_idx = state["current_page_index"]

        # Check if we've visited all pages
        if current_idx >= len(pages):
            return "end"

        # Check if research is complete
        if state.get("research_complete", False):
            return "end"

        return "continue"

    def _url_to_filename(self, url: str) -> str:
        """Convert URL to safe filename"""
        # Remove protocol
        filename = url.replace("https://", "").replace("http://", "")
        # Replace special chars
        filename = filename.replace("/", "_").replace("?", "_").replace("&", "_")
        # Limit length
        filename = filename[:50]
        return filename

    async def research(self, exploration_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the research workflow.

        Args:
            exploration_plan: Output from WebsiteScoper

        Returns:
            Research results with all collected data
        """
        print(f"\n{'='*70}")
        print(f"🔬 STARTING DEEP RESEARCH")
        print(f"{'='*70}")
        print(f"Topic: {exploration_plan['topic']}")
        print(f"Base URL: {exploration_plan['base_url']}")
        print(f"Pages to explore: {len(exploration_plan['pages_to_explore'])}")

        # Initialize state
        initial_state = ResearchState(
            exploration_plan=exploration_plan,
            current_page_index=0,
            visited_urls=[],
            page_contents=[],
            downloads=[],
            screenshots=[],
            messages=[],
            should_continue=True,
            research_complete=False
        )

        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)

        print(f"\n{'='*70}")
        print(f"✅ RESEARCH COMPLETE")
        print(f"{'='*70}")
        print(f"Pages visited: {len(final_state['visited_urls'])}")
        print(f"Content extracted: {len(final_state['page_contents'])} pages")
        print(f"Screenshots: {len(final_state['screenshots'])}")
        print(f"Downloads: {len(final_state['downloads'])}")

        return final_state


async def test_research_agent():
    """Test the research agent"""
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client
    from website_scoper import WebsiteScoper

    print("="*70)
    print("🧪 Testing Research Agent")
    print("="*70)

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            # Step 1: Scope the website
            scoper = WebsiteScoper(session)
            plan = await scoper.scope_website(
                url="https://docs.python.org/3/",
                research_topic="async programming and asyncio",
                max_pages=3  # Just 3 pages for testing
            )

            # Step 2: Research
            agent = ResearchAgent(session)
            results = await agent.research(plan)

            # Step 3: Show results
            print(f"\n{'='*70}")
            print("📊 RESEARCH RESULTS SUMMARY")
            print(f"{'='*70}")

            for i, content in enumerate(results['page_contents'], 1):
                print(f"\n{i}. {content['title']}")
                print(f"   URL: {content['url']}")
                print(f"   Length: {content['length']} chars")

                if 'synthesis' in content:
                    print(f"   Value: {content['synthesis'].get('value', 'unknown')}")
                    print(f"   Summary: {content['synthesis'].get('summary', '')[:100]}...")


if __name__ == "__main__":
    asyncio.run(test_research_agent())
