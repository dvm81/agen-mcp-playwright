"""
Comprehensive end-to-end test for deep_research.py

Tests the complete workflow with larger scope (10+ pages).
Use this for thorough validation before deployment.
"""

import asyncio
import sys
import os
import time

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deep_research import DeepWebsiteResearcher


async def full_test():
    """Comprehensive end-to-end test with larger scope"""

    print("\n" + "="*70)
    print("COMPREHENSIVE END-TO-END TEST")
    print("="*70)
    print("\n⚠  This test will take several minutes to complete")
    print("   Each test explores 8-12 pages with full content extraction\n")

    # More complex research scenarios
    test_cases = [
        {
            "url": "https://react.dev/",
            "topic": "hooks and component lifecycle",
            "max_pages": 10,
            "description": "Large site with extensive documentation"
        },
        {
            "url": "https://docs.langchain.com/",
            "topic": "chains and agents",
            "max_pages": 12,
            "description": "Technical documentation with code examples"
        },
        {
            "url": "https://playwright.dev/",
            "topic": "browser automation and testing",
            "max_pages": 8,
            "description": "API documentation and guides"
        }
    ]

    results_summary = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Full E2E Test {i}/{len(test_cases)}")
        print('='*70)
        print(f"URL: {test_case['url']}")
        print(f"Topic: {test_case['topic']}")
        print(f"Max pages: {test_case['max_pages']}")
        print(f"Description: {test_case['description']}")
        print('-'*70)

        start_time = time.time()

        try:
            researcher = DeepWebsiteResearcher()

            report_path = await researcher.research(
                url=test_case["url"],
                topic=test_case["topic"],
                max_pages=test_case["max_pages"]
            )

            elapsed = time.time() - start_time

            # Analyze report
            with open(report_path, 'r') as f:
                content = f.read()

            pages_documented = content.count('**URL**:')
            screenshots_count = content.count('📸')
            has_summary = '## Executive Summary' in content
            has_findings = '## Key Findings' in content
            has_methodology = '## Research Methodology' in content

            # Detailed validations
            validations = [
                ("Report file exists", os.path.exists(report_path)),
                ("Report has content", len(content) > 2000),
                ("Has executive summary", has_summary),
                ("Has key findings", has_findings),
                ("Has methodology", has_methodology),
                ("Pages documented", pages_documented >= test_case['max_pages'] // 2),
                ("Contains markdown", '**' in content and '#' in content),
                ("Has citations", '## All Pages Visited' in content)
            ]

            all_passed = all(v[1] for v in validations)

            result = {
                "test": i,
                "topic": test_case["topic"],
                "url": test_case["url"],
                "status": "✓ PASSED" if all_passed else "✗ FAILED",
                "report_path": report_path,
                "report_size": len(content),
                "pages_documented": pages_documented,
                "screenshots": screenshots_count,
                "elapsed_time": f"{elapsed:.1f}s",
                "elapsed_minutes": f"{elapsed/60:.1f}m",
                "validations": validations
            }

            print(f"\n{'✓' if all_passed else '✗'} Test {i} {'PASSED' if all_passed else 'FAILED'}")
            print(f"  Time: {result['elapsed_minutes']} ({result['elapsed_time']})")
            print(f"  Report: {report_path}")
            print(f"  Size: {len(content)} characters")
            print(f"  Pages: {pages_documented}")
            print(f"  Screenshots: {screenshots_count}")

            print(f"\n  Validations:")
            for check, passed in validations:
                print(f"    {'✓' if passed else '✗'} {check}")

        except Exception as e:
            elapsed = time.time() - start_time

            result = {
                "test": i,
                "topic": test_case["topic"],
                "url": test_case["url"],
                "status": "✗ FAILED",
                "error": str(e),
                "elapsed_time": f"{elapsed:.1f}s"
            }

            print(f"\n✗ Test {i} FAILED: {e}")
            print(f"  Time: {elapsed:.1f}s")

        results_summary.append(result)

    # Final summary
    print(f"\n{'='*70}")
    print("FINAL SUMMARY")
    print('='*70)

    passed = sum(1 for r in results_summary if "✓" in r['status'])
    total_time = sum(float(r.get('elapsed_time', '0s').rstrip('s'))
                     for r in results_summary)

    for result in results_summary:
        print(f"\n{result['status'].split()[0]} Test {result['test']}: {result['status'].split()[1]}")
        print(f"  Topic: {result['topic']}")
        print(f"  URL: {result['url']}")
        print(f"  Time: {result.get('elapsed_minutes', result.get('elapsed_time', 'N/A'))}")

        if result['status'] == "✓ PASSED":
            print(f"  Pages: {result['pages_documented']}")
            print(f"  Screenshots: {result['screenshots']}")
            print(f"  Report: {result['report_path']}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")

    print(f"\n{'='*70}")
    print(f"Results: {passed}/{len(test_cases)} tests passed")
    print(f"Total time: {total_time/60:.1f} minutes")
    print('='*70 + "\n")

    return passed == len(test_cases)


if __name__ == "__main__":
    success = asyncio.run(full_test())
    sys.exit(0 if success else 1)
