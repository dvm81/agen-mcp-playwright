"""
Test script for research_agent.py

Tests the LangGraph-powered research workflow.
Verifies state machine execution, content collection, and LLM synthesis.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from website_scoper import WebsiteScoper
from research_agent import ResearchAgent


async def test_research():
    """Test the research agent with LangGraph workflow"""

    scoper = WebsiteScoper()

    try:
        print("\n" + "="*70)
        print("RESEARCH AGENT TEST")
        print("="*70)

        # PHASE 1: Create exploration plan
        print("\n" + "-"*70)
        print("PHASE 1: Creating exploration plan")
        print("-"*70)

        plan = await scoper.scope_website(
            url="https://docs.python.org/3/",
            research_topic="asyncio and async programming",
            max_pages=3  # Keep small for testing
        )

        print(f"✓ Created plan with {len(plan['pages_to_explore'])} pages")
        for i, page in enumerate(plan['pages_to_explore'], 1):
            print(f"  {i}. {page['title']} [{page['priority']}]")

        # PHASE 2: Run research agent
        print("\n" + "-"*70)
        print("PHASE 2: Running research workflow")
        print("-"*70)

        agent = ResearchAgent(scoper.session)
        results = await agent.research(plan)

        # PHASE 3: Analyze results
        print("\n" + "-"*70)
        print("PHASE 3: Research Results")
        print("-"*70)

        print(f"\n✓ Pages visited: {len(results['visited_urls'])}")
        print(f"✓ Content extracted: {len(results['page_contents'])} pages")
        print(f"✓ Screenshots taken: {len(results['screenshots'])}")
        print(f"✓ Research complete: {results['research_complete']}")

        print("\n--- Visited URLs ---")
        for url in results['visited_urls']:
            print(f"  • {url}")

        print("\n--- Page Contents ---")
        for i, content in enumerate(results['page_contents'], 1):
            print(f"\n{i}. {content['url']}")
            print(f"   Priority: {content.get('priority', 'N/A')}")
            print(f"   Title: {content.get('title', 'N/A')}")
            print(f"   Content length: {len(content.get('content', ''))} chars")
            print(f"   Extraction method: {content.get('extraction_method', 'N/A')}")

            if 'synthesis' in content:
                synthesis = content['synthesis']
                print(f"   LLM Synthesis:")
                print(f"     Value: {synthesis.get('value_assessment', 'N/A')}")
                print(f"     Summary: {synthesis.get('summary', 'N/A')[:100]}...")
                print(f"     Key points: {len(synthesis.get('key_points', []))}")
                print(f"     Notable quotes: {len(synthesis.get('notable_quotes', []))}")

        print("\n--- Screenshots ---")
        if results['screenshots']:
            for screenshot in results['screenshots']:
                print(f"  📸 {screenshot}")
        else:
            print("  (none)")

        # Validation
        print("\n" + "-"*70)
        print("VALIDATION")
        print("-"*70)

        validations = []

        # Check all pages visited
        expected_pages = len(plan['pages_to_explore'])
        actual_pages = len(results['visited_urls'])
        if actual_pages == expected_pages:
            print(f"✓ All pages visited ({actual_pages}/{expected_pages})")
            validations.append(True)
        else:
            print(f"✗ Page count mismatch ({actual_pages}/{expected_pages})")
            validations.append(False)

        # Check content extracted
        if len(results['page_contents']) > 0:
            print(f"✓ Content extracted from {len(results['page_contents'])} pages")
            validations.append(True)
        else:
            print("✗ No content extracted")
            validations.append(False)

        # Check synthesis
        synthesized_pages = sum(1 for p in results['page_contents'] if 'synthesis' in p)
        if synthesized_pages > 0:
            print(f"✓ LLM synthesis for {synthesized_pages} pages")
            validations.append(True)
        else:
            print("✗ No LLM synthesis found")
            validations.append(False)

        # Check research complete flag
        if results['research_complete']:
            print("✓ Research marked as complete")
            validations.append(True)
        else:
            print("✗ Research not marked as complete")
            validations.append(False)

        # Save full results for inspection
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, 'research_results.json')

        # Make a serializable copy
        serializable_results = {
            'exploration_plan': results['exploration_plan'],
            'visited_urls': results['visited_urls'],
            'page_contents': results['page_contents'],
            'screenshots': results['screenshots'],
            'research_complete': results['research_complete']
        }

        with open(output_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\n✓ Full results saved to: {output_file}")

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        all_passed = all(validations)
        status = "PASSED" if all_passed else "FAILED"
        status_icon = "✓" if all_passed else "✗"

        print(f"\n{status_icon} Test {status}")
        print(f"  Validations: {sum(validations)}/{len(validations)} passed")
        print(f"  Pages visited: {len(results['visited_urls'])}")
        print(f"  Content collected: {len(results['page_contents'])}")
        print(f"  Screenshots: {len(results['screenshots'])}")
        print(f"  Results saved: {output_file}")

        print("\n" + "="*70 + "\n")

        return all_passed

    finally:
        await scoper.close()


if __name__ == "__main__":
    success = asyncio.run(test_research())
    sys.exit(0 if success else 1)
