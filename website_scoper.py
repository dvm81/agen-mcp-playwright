#!/usr/bin/env python3
"""
Website Scoper - Analyzes a website and creates an exploration plan

This module:
1. Visits a website's homepage
2. Extracts navigation structure and links
3. Uses LLM to identify relevant sections for research topic
4. Creates a prioritized exploration plan
"""

import asyncio
import json
import re
from typing import Dict, List, Any
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


class WebsiteScoper:
    """Analyze website structure and create research plan"""

    def __init__(self, mcp_session: ClientSession, llm_model: str = "gpt-4o"):
        self.session = mcp_session
        self.llm = ChatOpenAI(model=llm_model, temperature=0)

    async def scope_website(self, url: str, research_topic: str, max_pages: int = 15) -> Dict[str, Any]:
        """
        Analyze website and create exploration plan.

        Args:
            url: Website homepage URL
            research_topic: What to research about
            max_pages: Maximum pages to explore

        Returns:
            {
                'base_url': str,
                'topic': str,
                'pages_to_explore': [
                    {'url': str, 'priority': str, 'reason': str},
                    ...
                ],
                'estimated_relevance': float
            }
        """
        print(f"\n{'='*70}")
        print(f"🔍 SCOPING WEBSITE")
        print(f"{'='*70}")
        print(f"URL: {url}")
        print(f"Topic: {research_topic}")
        print(f"Max pages: {max_pages}")

        # Step 1: Navigate to homepage
        print(f"\n📍 Step 1: Visiting homepage...")
        await self.session.call_tool("browser_navigate", {"url": url})

        # Step 2: Extract page structure and links
        print(f"📊 Step 2: Analyzing page structure...")
        structure = await self._extract_page_structure()

        # Step 3: Use LLM to identify relevant sections
        print(f"🤖 Step 3: LLM analyzing relevance...")
        exploration_plan = await self._create_exploration_plan(
            url,
            research_topic,
            structure,
            max_pages
        )

        print(f"\n✅ Scoping complete!")
        print(f"   Relevant pages found: {len(exploration_plan['pages_to_explore'])}")
        print(f"   Estimated relevance: {exploration_plan['estimated_relevance']:.0%}")

        return exploration_plan

    async def _extract_page_structure(self) -> Dict[str, Any]:
        """Extract links and structure from current page"""

        # Get page snapshot for structure
        snapshot_result = await self.session.call_tool("browser_snapshot", {})

        # Extract links using JavaScript
        links_js = """
        (() => {
            const links = Array.from(document.querySelectorAll('a'))
                .filter(a => a.href && a.innerText)
                .filter(a => !a.href.includes('javascript:'))
                .filter(a => !a.href.includes('mailto:'))
                .filter(a => !a.href.includes('#'))
                .slice(0, 50)  // Limit to 50 links
                .map(a => ({
                    text: a.innerText.trim().slice(0, 100),
                    url: a.href,
                    context: (a.closest('nav') ? 'nav' :
                             a.closest('header') ? 'header' :
                             a.closest('footer') ? 'footer' : 'content')
                }));

            return {
                title: document.title,
                url: window.location.href,
                links: links,
                headings: Array.from(document.querySelectorAll('h1, h2, h3'))
                    .map(h => ({
                        level: h.tagName,
                        text: h.innerText.trim().slice(0, 100)
                    }))
                    .slice(0, 20)
            };
        })()
        """

        result = await self.session.call_tool("browser_evaluate", {"expression": links_js})

        # Parse the result
        structure = {
            'title': '',
            'url': '',
            'links': [],
            'headings': []
        }

        for item in result.content:
            if hasattr(item, 'text'):
                # The result contains the page structure
                # This is a simplified parser - you may need to improve it
                text = item.text

                # Try to extract structured data
                # Look for links in the response
                url_pattern = r'https?://[^\s,\'"}\]]+|/[^\s,\'"}\]]+'
                urls = re.findall(url_pattern, text)

                # Create basic structure from found URLs
                for url in urls[:30]:  # Limit to 30 URLs
                    if url and not url.endswith(('.jpg', '.png', '.gif', '.css', '.js')):
                        structure['links'].append({
                            'text': '',
                            'url': url,
                            'context': 'content'
                        })

        print(f"   Found {len(structure['links'])} links")

        return structure

    async def _create_exploration_plan(
        self,
        base_url: str,
        research_topic: str,
        structure: Dict[str, Any],
        max_pages: int
    ) -> Dict[str, Any]:
        """Use LLM to create exploration plan based on structure"""

        # Prepare context for LLM
        links_summary = "\n".join([
            f"- [{link.get('text', 'Link')}]({link['url']}) (context: {link.get('context', 'unknown')})"
            for link in structure['links'][:50]  # Limit to 50 for LLM
        ])

        headings_summary = "\n".join([
            f"- {h.get('level', 'H?')}: {h.get('text', '')}"
            for h in structure.get('headings', [])[:20]
        ])

        system_prompt = """You are a research planning assistant. Given a website's structure and a research topic,
identify the most relevant pages to explore.

Your task:
1. Analyze the available links and headings
2. Identify which pages are most relevant to the research topic
3. Prioritize pages (high/medium/low)
4. Provide a reason for each selection
5. Estimate overall relevance (0-1) of this website for the topic

Return a JSON object with this structure:
{
    "pages_to_explore": [
        {
            "url": "full URL",
            "priority": "high|medium|low",
            "reason": "why this page is relevant"
        }
    ],
    "estimated_relevance": 0.85,
    "key_sections": ["section name 1", "section name 2"]
}

Focus on:
- Documentation, tutorials, guides
- Technical content over marketing
- Unique content over generic pages (skip: about, contact, privacy)
- Limit to the most valuable pages
"""

        user_prompt = f"""Research Topic: {research_topic}

Website: {base_url}
Title: {structure.get('title', 'Unknown')}

Available Links:
{links_summary if links_summary else '(No links found)'}

Headings on page:
{headings_summary if headings_summary else '(No headings found)'}

Please identify the top {max_pages} most relevant pages to explore for this research topic.
Return valid JSON only."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # Call LLM
        response = self.llm.invoke(messages)
        response_text = response.content

        # Parse JSON response
        try:
            # Extract JSON from markdown code blocks if present
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()

            plan = json.loads(json_str)

            # Ensure we have required fields
            if 'pages_to_explore' not in plan:
                plan['pages_to_explore'] = []
            if 'estimated_relevance' not in plan:
                plan['estimated_relevance'] = 0.5

            # Add base info
            plan['base_url'] = base_url
            plan['topic'] = research_topic
            plan['max_pages'] = max_pages

            # Limit to max_pages
            plan['pages_to_explore'] = plan['pages_to_explore'][:max_pages]

            return plan

        except json.JSONDecodeError as e:
            print(f"⚠️  Warning: Could not parse LLM response as JSON: {e}")
            print(f"Response was: {response_text[:200]}...")

            # Return a basic plan
            return {
                'base_url': base_url,
                'topic': research_topic,
                'max_pages': max_pages,
                'pages_to_explore': [
                    {'url': base_url, 'priority': 'high', 'reason': 'Homepage'}
                ],
                'estimated_relevance': 0.3,
                'key_sections': []
            }


async def test_scoper():
    """Test the website scoper"""
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client

    print("="*70)
    print("🧪 Testing Website Scoper")
    print("="*70)

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            scoper = WebsiteScoper(session)

            # Test with Python docs
            result = await scoper.scope_website(
                url="https://docs.python.org/3/",
                research_topic="async programming and asyncio",
                max_pages=10
            )

            print(f"\n{'='*70}")
            print("📋 SCOPING RESULTS")
            print(f"{'='*70}")
            print(f"Base URL: {result['base_url']}")
            print(f"Topic: {result['topic']}")
            print(f"Relevance: {result['estimated_relevance']:.0%}")

            if result.get('key_sections'):
                print(f"\nKey Sections: {', '.join(result['key_sections'])}")

            print(f"\nPages to Explore ({len(result['pages_to_explore'])}):")
            for i, page in enumerate(result['pages_to_explore'], 1):
                print(f"\n{i}. [{page['priority'].upper()}] {page['url']}")
                print(f"   Reason: {page['reason']}")


if __name__ == "__main__":
    asyncio.run(test_scoper())
