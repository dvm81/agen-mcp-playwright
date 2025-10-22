"""
Quick end-to-end test for deep_research.py

Tests the complete workflow with small scope (3-5 pages).
Use this for fast validation during development.
"""

import asyncio
import sys
import os
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deep_research import DeepWebsiteResearcher


async def quick_test():
    """Quick end-to-end test with small scope"""

    print("\n" + "="*70)
    print("QUICK END-TO-END TEST")
    print("="*70)

    # Test cases with limited scope for speed
    test_cases = [
        {
            "url": "https://fastapi.tiangolo.com/",
            "topic": "dependency injection",
            "max_pages": 3,
            "description": "FastAPI dependency injection documentation"
        },
        {
            "url": "https://docs.python.org/3/",
            "topic": "decorators",
            "max_pages": 4,
            "description": "Python decorators documentation"
        }
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}/{len(test_cases)}: {test_case['topic']}")
        print(f"URL: {test_case['url']}")
        print(f"Max pages: {test_case['max_pages']}")
        print(f"Description: {test_case['description']}")
        print('='*70)

        start_time = time.time()

        try:
            researcher = DeepWebsiteResearcher()

            report_path = await researcher.research(
                url=test_case["url"],
                topic=test_case["topic"],
                max_pages=test_case["max_pages"]
            )

            elapsed = time.time() - start_time

            # Validate report
            with open(report_path, 'r') as f:
                content = f.read()

            pages_documented = content.count('**URL**:')
            has_summary = '## Executive Summary' in content
            has_findings = '## Key Findings' in content
            has_methodology = '## Research Methodology' in content

            # Check report quality
            validations = [
                ("Report exists", os.path.exists(report_path)),
                ("Has content", len(content) > 1000),
                ("Has executive summary", has_summary),
                ("Has key findings", has_findings),
                ("Has methodology", has_methodology),
                ("Pages documented", pages_documented > 0)
            ]

            all_passed = all(v[1] for v in validations)

            print(f"\n{'✓' if all_passed else '✗'} Test {i} {'PASSED' if all_passed else 'FAILED'}")
            print(f"  Time: {elapsed:.1f}s")
            print(f"  Report: {report_path}")
            print(f"  Size: {len(content)} characters")
            print(f"  Pages: {pages_documented}")

            print(f"\n  Validations:")
            for check, passed in validations:
                print(f"    {'✓' if passed else '✗'} {check}")

            results.append({
                'test': i,
                'topic': test_case['topic'],
                'status': 'PASSED' if all_passed else 'FAILED',
                'elapsed': elapsed,
                'report_path': report_path,
                'report_size': len(content),
                'pages_documented': pages_documented,
                'validations': validations
            })

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"\n✗ Test {i} FAILED: {e}")

            results.append({
                'test': i,
                'topic': test_case['topic'],
                'status': 'FAILED',
                'elapsed': elapsed,
                'error': str(e)
            })

    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print('='*70)

    passed_count = sum(1 for r in results if r['status'] == 'PASSED')

    for result in results:
        status_icon = "✓" if result['status'] == 'PASSED' else "✗"
        print(f"\n{status_icon} Test {result['test']}: {result['status']}")
        print(f"  Topic: {result['topic']}")
        print(f"  Time: {result['elapsed']:.1f}s")

        if result['status'] == 'PASSED':
            print(f"  Pages: {result['pages_documented']}")
            print(f"  Report: {result['report_path']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")

    print(f"\n{'='*70}")
    print(f"Results: {passed_count}/{len(test_cases)} tests passed")
    print('='*70 + "\n")

    return passed_count == len(test_cases)


if __name__ == "__main__":
    success = asyncio.run(quick_test())
    sys.exit(0 if success else 1)
