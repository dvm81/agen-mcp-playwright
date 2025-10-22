"""
Test script for website_scoper.py

Tests website analysis and exploration plan generation.
Verifies LLM-powered page identification, prioritization, and relevance scoring.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from website_scoper import WebsiteScoper


async def test_scoping():
    """Test website scoping and exploration planning"""

    scoper = WebsiteScoper()

    try:
        # Test different websites and research topics
        test_cases = [
            {
                "url": "https://docs.python.org/3/",
                "topic": "asyncio and async programming",
                "max_pages": 5
            },
            {
                "url": "https://fastapi.tiangolo.com/",
                "topic": "dependency injection and routing",
                "max_pages": 6
            },
            {
                "url": "https://react.dev/",
                "topic": "hooks and state management",
                "max_pages": 4
            }
        ]

        print("\n" + "="*70)
        print("WEBSITE SCOPER TEST")
        print("="*70)

        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n[Test {i}/{len(test_cases)}] Topic: {test_case['topic']}")
            print(f"URL: {test_case['url']}")
            print(f"Max pages: {test_case['max_pages']}")
            print("-" * 70)

            try:
                plan = await scoper.scope_website(
                    url=test_case["url"],
                    research_topic=test_case["topic"],
                    max_pages=test_case["max_pages"]
                )

                # Display results
                print(f"\n✓ Base URL: {plan['base_url']}")
                print(f"✓ Research Topic: {plan['research_topic']}")
                print(f"✓ Pages to explore: {len(plan['pages_to_explore'])}")
                print(f"✓ Estimated relevance: {plan['estimated_relevance']}%")
                print(f"✓ Reasoning: {plan['reasoning'][:150]}...")

                print(f"\n--- Exploration Plan ---")
                for j, page in enumerate(plan['pages_to_explore'], 1):
                    print(f"{j}. [{page['priority']}] {page['title']}")
                    print(f"   URL: {page['url']}")
                    print(f"   Reason: {page['reason'][:80]}...")
                    print()

                # Validate plan
                assert len(plan['pages_to_explore']) <= test_case['max_pages'], \
                    f"Too many pages: {len(plan['pages_to_explore'])} > {test_case['max_pages']}"
                assert plan['estimated_relevance'] >= 50, \
                    f"Low relevance: {plan['estimated_relevance']}%"
                assert all(p['priority'] in ['HIGH', 'MEDIUM', 'LOW']
                          for p in plan['pages_to_explore']), \
                    "Invalid priority values"

                # Save plan to file for inspection
                output_dir = os.path.join(os.path.dirname(__file__), 'output')
                os.makedirs(output_dir, exist_ok=True)
                filename = os.path.join(output_dir, f'plan_{i}.json')

                with open(filename, 'w') as f:
                    json.dump(plan, f, indent=2)
                print(f"✓ Full plan saved to: {filename}")

                results.append({
                    'test_case': test_case,
                    'status': 'PASSED',
                    'pages_found': len(plan['pages_to_explore']),
                    'relevance': plan['estimated_relevance'],
                    'plan_file': filename
                })

            except Exception as e:
                print(f"\n✗ FAILED: {e}")
                results.append({
                    'test_case': test_case,
                    'status': 'FAILED',
                    'error': str(e)
                })

        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        passed = sum(1 for r in results if r['status'] == 'PASSED')

        for i, result in enumerate(results, 1):
            status_icon = "✓" if result['status'] == 'PASSED' else "✗"
            print(f"\n{status_icon} Test {i}: {result['status']}")
            print(f"  Topic: {result['test_case']['topic']}")
            print(f"  URL: {result['test_case']['url']}")

            if result['status'] == 'PASSED':
                print(f"  Pages found: {result['pages_found']}/{result['test_case']['max_pages']}")
                print(f"  Relevance: {result['relevance']}%")
                print(f"  Plan saved: {result['plan_file']}")
            else:
                print(f"  Error: {result.get('error', 'Unknown')}")

        print("\n" + "="*70)
        print(f"Results: {passed}/{len(test_cases)} tests passed")
        print("="*70 + "\n")

        return passed == len(test_cases)

    finally:
        await scoper.close()


if __name__ == "__main__":
    success = asyncio.run(test_scoping())
    sys.exit(0 if success else 1)
