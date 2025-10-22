#!/usr/bin/env python3
"""
Report Generator - Creates comprehensive markdown reports from research findings

This module:
1. Takes research results from the ResearchAgent
2. Organizes content by relevance and topic
3. Uses LLM to generate executive summary
4. Creates formatted markdown report
5. Includes citations, screenshots, and downloads
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage


class ReportGenerator:
    """Generate comprehensive research reports"""

    def __init__(self, llm_model: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=llm_model, temperature=0.3)
        self.output_dir = Path("research_outputs")
        self.output_dir.mkdir(exist_ok=True)

    async def generate_report(self, research_results: Dict[str, Any]) -> str:
        """
        Generate comprehensive markdown report from research results.

        Args:
            research_results: Output from ResearchAgent.research()

        Returns:
            Path to generated report file
        """
        plan = research_results["exploration_plan"]
        pages = research_results["page_contents"]
        screenshots = research_results["screenshots"]
        downloads = research_results["downloads"]
        visited_urls = research_results["visited_urls"]

        print(f"\n{'='*70}")
        print(f"📝 GENERATING RESEARCH REPORT")
        print(f"{'='*70}")

        # Generate report sections
        report_parts = []

        # 1. Header and metadata
        header = self._generate_header(plan, pages, screenshots, downloads)
        report_parts.append(header)

        # 2. Executive Summary (LLM-generated)
        print("🤖 Generating executive summary...")
        summary = await self._generate_executive_summary(plan, pages)
        report_parts.append(summary)

        # 3. Key Findings (organized by relevance)
        print("📊 Organizing key findings...")
        findings = self._generate_findings_section(pages)
        report_parts.append(findings)

        # 4. Detailed Page Summaries
        print("📄 Creating page summaries...")
        page_summaries = self._generate_page_summaries(pages)
        report_parts.append(page_summaries)

        # 5. Resources Collected
        print("📦 Listing resources...")
        resources = self._generate_resources_section(screenshots, downloads)
        report_parts.append(resources)

        # 6. All Pages Visited
        print("🔗 Adding citations...")
        citations = self._generate_citations(visited_urls, pages)
        report_parts.append(citations)

        # 7. Methodology
        methodology = self._generate_methodology()
        report_parts.append(methodology)

        # Combine all parts
        full_report = "\n\n".join(report_parts)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = self._sanitize_filename(plan["topic"])
        filename = f"research_report_{safe_topic}_{timestamp}.md"
        filepath = self.output_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_report)

        print(f"\n✅ Report generated: {filepath}")
        print(f"   Size: {len(full_report):,} characters")

        return str(filepath)

    def _generate_header(
        self,
        plan: Dict[str, Any],
        pages: List[Dict],
        screenshots: List[str],
        downloads: List[str]
    ) -> str:
        """Generate report header with metadata"""
        timestamp = datetime.now().strftime("%B %d, %Y at %H:%M")

        header = f"""# Deep Research Report: {plan['topic']}

**Generated**: {timestamp}
**Base URL**: {plan['base_url']}
**Pages Explored**: {len(pages)}
**Screenshots**: {len(screenshots)}
**Files Downloaded**: {len(downloads)}
**Estimated Relevance**: {plan.get('estimated_relevance', 0):.0%}

---
"""
        return header

    async def _generate_executive_summary(
        self,
        plan: Dict[str, Any],
        pages: List[Dict]
    ) -> str:
        """Use LLM to generate executive summary"""

        # Collect all valuable content
        valuable_content = []
        for page in pages:
            if page.get('synthesis', {}).get('value') == 'yes':
                valuable_content.append({
                    'url': page['url'],
                    'title': page['title'],
                    'summary': page.get('synthesis', {}).get('summary', ''),
                    'key_points': page.get('synthesis', {}).get('key_points', [])
                })

        if not valuable_content:
            return """## Executive Summary

No valuable content was found during the research. The explored pages may not have contained relevant information about the research topic.
"""

        # Prepare content for LLM
        content_summary = "\n\n".join([
            f"**{c['title']}**\n{c['summary']}\nKey points: {', '.join(c['key_points'][:3])}"
            for c in valuable_content[:5]  # Limit to top 5
        ])

        prompt = f"""Based on the following research findings about "{plan['topic']}",
write a comprehensive 2-3 paragraph executive summary that:
1. Highlights the main discoveries
2. Synthesizes key themes across the sources
3. Provides actionable insights

Research Findings:
{content_summary}

Write a clear, professional executive summary:"""

        try:
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            summary_text = response.content

            return f"""## Executive Summary

{summary_text}

---
"""
        except Exception as e:
            print(f"⚠️  Summary generation failed: {e}")
            return """## Executive Summary

Research findings have been collected and organized in the sections below.

---
"""

    def _generate_findings_section(self, pages: List[Dict]) -> str:
        """Generate key findings section organized by value"""

        # Separate by value
        high_value = [p for p in pages if p.get('synthesis', {}).get('value') == 'yes']
        medium_value = [p for p in pages if p.get('synthesis', {}).get('value') == 'somewhat']

        if not high_value and not medium_value:
            return """## Key Findings

No significant findings were extracted from the explored pages.
"""

        findings = ["## Key Findings\n"]

        # High value findings
        if high_value:
            findings.append("### High-Value Discoveries\n")
            for i, page in enumerate(high_value, 1):
                synthesis = page.get('synthesis', {})
                key_points = synthesis.get('key_points', [])

                findings.append(f"**{i}. {page['title']}**")
                findings.append(f"*Source: [{page['url']}]({page['url']})*\n")

                if key_points:
                    for point in key_points:
                        findings.append(f"- {point}")
                    findings.append("")

                if synthesis.get('quotes'):
                    findings.append("**Notable Quotes:**")
                    for quote in synthesis['quotes'][:2]:
                        findings.append(f"> {quote}\n")

        # Medium value findings
        if medium_value:
            findings.append("\n### Additional Insights\n")
            for page in medium_value:
                synthesis = page.get('synthesis', {})
                findings.append(f"- **{page['title']}**: {synthesis.get('summary', 'No summary available')}")

        findings.append("\n---\n")
        return "\n".join(findings)

    def _generate_page_summaries(self, pages: List[Dict]) -> str:
        """Generate detailed summaries for each page"""

        summaries = ["## Detailed Page Analysis\n"]

        for i, page in enumerate(pages, 1):
            synthesis = page.get('synthesis', {})

            summaries.append(f"### {i}. {page['title']}")
            summaries.append(f"**URL**: {page['url']}")
            summaries.append(f"**Priority**: {page.get('priority', 'unknown').upper()}")
            summaries.append(f"**Content Length**: {page['length']:,} characters")
            summaries.append(f"**Extraction Method**: {page['method']}")
            summaries.append(f"**Value Assessment**: {synthesis.get('value', 'unknown')}\n")

            if synthesis.get('summary'):
                summaries.append(f"**Summary**: {synthesis['summary']}\n")

            if synthesis.get('key_points'):
                summaries.append("**Key Points:**")
                for point in synthesis['key_points']:
                    summaries.append(f"- {point}")
                summaries.append("")

            # Add content preview
            content_preview = page.get('content', '')[:500]
            if content_preview:
                summaries.append(f"**Content Preview:**")
                summaries.append(f"```")
                summaries.append(content_preview + "...")
                summaries.append(f"```\n")

            summaries.append("---\n")

        return "\n".join(summaries)

    def _generate_resources_section(
        self,
        screenshots: List[str],
        downloads: List[str]
    ) -> str:
        """Generate resources section"""

        resources = ["## Resources Collected\n"]

        if screenshots:
            resources.append("### Screenshots\n")
            for screenshot in screenshots:
                filename = Path(screenshot).name
                resources.append(f"- 📸 `{filename}`")
            resources.append("")

        if downloads:
            resources.append("### Downloaded Files\n")
            for download in downloads:
                filename = Path(download).name
                resources.append(f"- 📄 `{filename}`")
            resources.append("")

        if not screenshots and not downloads:
            resources.append("No additional resources were collected during this research.\n")

        resources.append("---\n")
        return "\n".join(resources)

    def _generate_citations(
        self,
        visited_urls: List[str],
        pages: List[Dict]
    ) -> str:
        """Generate citations section"""

        citations = ["## All Pages Visited\n"]

        for i, url in enumerate(visited_urls, 1):
            # Find corresponding page data
            page_data = next((p for p in pages if p['url'] == url), None)

            if page_data:
                title = page_data['title']
                value = page_data.get('synthesis', {}).get('value', 'unknown')
                emoji = "✅" if value == "yes" else "⚠️" if value == "somewhat" else "❌"

                citations.append(f"{i}. {emoji} [{title}]({url})")
            else:
                citations.append(f"{i}. [{url}]({url})")

        citations.append("\n---\n")
        return "\n".join(citations)

    def _generate_methodology(self) -> str:
        """Generate methodology section"""

        methodology = """## Research Methodology

This report was generated using an automated deep research agent with the following process:

1. **Scoping Phase**: The website was analyzed to identify relevant sections and pages related to the research topic. An LLM (GPT-4) assessed the site structure and created a prioritized exploration plan.

2. **Exploration Phase**: Each identified page was visited using browser automation (Playwright). A LangGraph state machine coordinated the workflow:
   - Navigate to page
   - Extract clean content (removing ads, navigation, etc.)
   - Collect resources (screenshots, downloadable files)
   - Synthesize findings using LLM analysis

3. **Synthesis Phase**: The LLM analyzed each page's content to extract:
   - Key points relevant to the research topic
   - Notable quotes and facts
   - Value assessment (high/medium/low relevance)

4. **Report Generation**: All findings were aggregated, organized by relevance, and formatted into this comprehensive report.

**Tools Used**:
- Browser Automation: Playwright MCP Server
- Content Extraction: Custom web extractor with accessibility snapshots
- AI Analysis: OpenAI GPT-4o
- Workflow Orchestration: LangGraph state machine

**Limitations**:
- Only pages within the specified website were explored
- Content extraction may miss dynamic or JavaScript-rendered content
- LLM analysis is based on extracted text only, not visual elements
- Some pages may have been inaccessible due to authentication or rate limiting

---

*Report generated by Deep Website Research Agent*
"""
        return methodology

    def _sanitize_filename(self, text: str) -> str:
        """Convert text to safe filename"""
        # Remove/replace unsafe characters
        safe = text.lower()
        safe = safe.replace(" ", "_")
        safe = "".join(c for c in safe if c.isalnum() or c in "_-")
        # Limit length
        safe = safe[:50]
        return safe


async def test_report_generator():
    """Test the report generator with sample data"""

    # Create sample research results
    sample_results = {
        "exploration_plan": {
            "base_url": "https://docs.python.org/3/",
            "topic": "asyncio and async programming",
            "estimated_relevance": 0.95,
            "max_pages": 3
        },
        "visited_urls": [
            "https://docs.python.org/3/library/asyncio.html",
            "https://docs.python.org/3/howto/async.html"
        ],
        "page_contents": [
            {
                "url": "https://docs.python.org/3/library/asyncio.html",
                "title": "asyncio — Asynchronous I/O",
                "content": "asyncio is a library to write concurrent code using async/await syntax...",
                "length": 5000,
                "method": "snapshot",
                "priority": "high",
                "synthesis": {
                    "value": "yes",
                    "summary": "Comprehensive documentation of asyncio library for concurrent programming",
                    "key_points": [
                        "asyncio provides async/await syntax support",
                        "Includes event loop for managing async tasks",
                        "Supports network I/O and subprocess communication"
                    ],
                    "quotes": [
                        "asyncio is used as a foundation for multiple Python asynchronous frameworks"
                    ]
                }
            },
            {
                "url": "https://docs.python.org/3/howto/async.html",
                "title": "Async How-To",
                "content": "Brief intro...",
                "length": 100,
                "method": "javascript",
                "priority": "medium",
                "synthesis": {
                    "value": "somewhat",
                    "summary": "Brief introduction to async concepts",
                    "key_points": ["Basic async syntax"],
                    "quotes": []
                }
            }
        ],
        "screenshots": [
            "research_outputs/asyncio_screenshot.png"
        ],
        "downloads": []
    }

    generator = ReportGenerator()
    report_path = await generator.generate_report(sample_results)

    print(f"\n✅ Test report generated: {report_path}")

    # Show preview
    with open(report_path, 'r') as f:
        content = f.read()
        print(f"\n📄 Report Preview (first 1000 chars):")
        print("="*70)
        print(content[:1000])
        print("...")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_report_generator())
