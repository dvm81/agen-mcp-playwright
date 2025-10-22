#!/usr/bin/env python3
"""
Deep Website Research - Main Orchestrator

Simple API for deep website research:
    researcher = DeepWebsiteResearcher()
    report = await researcher.research(
        url="https://docs.python.org/3/",
        topic="asyncio and async programming",
        max_pages=10
    )

Output: Comprehensive markdown report in research_outputs/
"""

import asyncio
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from website_scoper import WebsiteScoper
from research_agent import ResearchAgent
from report_generator import ReportGenerator

load_dotenv()


class DeepWebsiteResearcher:
    """
    Complete deep website research workflow.

    Combines scoping, exploration, and reporting into one simple API.
    """

    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm_model = llm_model
        self.session: Optional[ClientSession] = None
        self.stdio_context = None

    async def __aenter__(self):
        """Start Playwright MCP server"""
        server_params = StdioServerParameters(
            command="npx",
            args=["-y", "@playwright/mcp@latest"],
            env=None
        )

        self.stdio_context = stdio_client(server_params)
        stdio, write = await self.stdio_context.__aenter__()

        self.session = ClientSession(stdio, write)
        await self.session.initialize()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Playwright MCP server"""
        if self.stdio_context:
            await self.stdio_context.__aexit__(exc_type, exc_val, exc_tb)

    async def research(
        self,
        url: str,
        topic: str,
        max_pages: int = 10
    ) -> str:
        """
        Conduct deep research on a website.

        Args:
            url: Website homepage URL
            topic: Research topic/question
            max_pages: Maximum pages to explore (default: 10)

        Returns:
            Path to generated markdown report

        Example:
            async with DeepWebsiteResearcher() as researcher:
                report_path = await researcher.research(
                    url="https://langchain.com/docs",
                    topic="How to build agents with LangGraph",
                    max_pages=15
                )
                print(f"Report: {report_path}")
        """
        print(f"\n{'='*70}")
        print(f"🔬 DEEP WEBSITE RESEARCH")
        print(f"{'='*70}")
        print(f"URL: {url}")
        print(f"Topic: {topic}")
        print(f"Max pages: {max_pages}")
        print(f"{'='*70}\n")

        # Phase 1: Scoping
        print("PHASE 1: SCOPING")
        print("-" * 70)
        scoper = WebsiteScoper(self.session, self.llm_model)
        exploration_plan = await scoper.scope_website(url, topic, max_pages)

        # Phase 2: Research
        print(f"\nPHASE 2: EXPLORATION")
        print("-" * 70)
        agent = ResearchAgent(self.session, self.llm_model)
        research_results = await agent.research(exploration_plan)

        # Phase 3: Report Generation
        print(f"\nPHASE 3: REPORT GENERATION")
        print("-" * 70)
        generator = ReportGenerator(self.llm_model)
        report_path = await generator.generate_report(research_results)

        print(f"\n{'='*70}")
        print(f"✅ RESEARCH COMPLETE!")
        print(f"{'='*70}")
        print(f"📄 Report: {report_path}")
        print(f"📊 Pages explored: {len(research_results['visited_urls'])}")
        print(f"📸 Screenshots: {len(research_results['screenshots'])}")
        print(f"{'='*70}\n")

        return report_path


async def main():
    """
    Example usage of the Deep Website Researcher
    """
    print("="*70)
    print("🧪 Testing Deep Website Research")
    print("="*70)

    # Example 1: Python asyncio documentation
    async with DeepWebsiteResearcher() as researcher:
        report = await researcher.research(
            url="https://docs.python.org/3/",
            topic="asyncio and async programming",
            max_pages=5  # Keep it small for testing
        )

        print(f"\n✅ Research complete!")
        print(f"\nTo view the report:")
        print(f"  cat {report}")
        print(f"\nOr open in your editor:")
        print(f"  code {report}")

    # Uncomment to test more examples:

    # # Example 2: LangChain documentation
    # async with DeepWebsiteResearcher() as researcher:
    #     report = await researcher.research(
    #         url="https://python.langchain.com/docs/",
    #         topic="How to build agents with LangGraph",
    #         max_pages=10
    #     )

    # # Example 3: FastAPI documentation
    # async with DeepWebsiteResearcher() as researcher:
    #     report = await researcher.research(
    #         url="https://fastapi.tiangolo.com/",
    #         topic="async endpoint implementation and performance",
    #         max_pages=8
    #     )


if __name__ == "__main__":
    asyncio.run(main())
