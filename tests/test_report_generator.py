"""
Test script for report_generator.py

Tests markdown report generation from research results.
Verifies all sections are present and properly formatted.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_generator import ReportGenerator


async def test_report_generation():
    """Test report generation with sample data"""

    print("\n" + "="*70)
    print("REPORT GENERATOR TEST")
    print("="*70)

    # Try to load existing research results
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    results_file = os.path.join(output_dir, 'research_results.json')

    try:
        with open(results_file, 'r') as f:
            research_results = json.load(f)
        print(f"\n✓ Loaded existing research results from {results_file}")
    except FileNotFoundError:
        # Create minimal sample data for testing
        print("\n⚠ No existing results found, creating sample data")
        research_results = {
            'exploration_plan': {
                'base_url': 'https://docs.python.org/3/',
                'research_topic': 'asyncio and async programming',
                'pages_to_explore': [
                    {
                        'url': 'https://docs.python.org/3/library/asyncio.html',
                        'title': 'asyncio — Asynchronous I/O',
                        'priority': 'HIGH',
                        'reason': 'Core asyncio documentation'
                    },
                    {
                        'url': 'https://docs.python.org/3/howto/async.html',
                        'title': 'Async How-To',
                        'priority': 'MEDIUM',
                        'reason': 'Introduction to async concepts'
                    }
                ],
                'estimated_relevance': 95,
                'reasoning': 'These pages provide comprehensive coverage of asyncio'
            },
            'visited_urls': [
                'https://docs.python.org/3/library/asyncio.html',
                'https://docs.python.org/3/howto/async.html'
            ],
            'page_contents': [
                {
                    'url': 'https://docs.python.org/3/library/asyncio.html',
                    'title': 'asyncio — Asynchronous I/O',
                    'priority': 'HIGH',
                    'content': 'asyncio is a library to write concurrent code using async/await syntax. It provides event loops, coroutines, tasks, and more for asynchronous programming in Python.',
                    'extraction_method': 'snapshot',
                    'synthesis': {
                        'value_assessment': 'yes',
                        'summary': 'Comprehensive documentation of asyncio library for concurrent programming',
                        'key_points': [
                            'asyncio provides async/await syntax support',
                            'Includes event loop for managing async tasks',
                            'Supports network I/O and subprocess communication'
                        ],
                        'notable_quotes': [
                            'asyncio is used as a foundation for multiple Python asynchronous frameworks'
                        ]
                    }
                },
                {
                    'url': 'https://docs.python.org/3/howto/async.html',
                    'title': 'Async How-To',
                    'priority': 'MEDIUM',
                    'content': 'Brief introduction to async concepts and how to use them effectively.',
                    'extraction_method': 'javascript',
                    'synthesis': {
                        'value_assessment': 'somewhat',
                        'summary': 'Brief introduction to async concepts',
                        'key_points': [
                            'Basic async syntax',
                            'Common patterns'
                        ],
                        'notable_quotes': []
                    }
                }
            ],
            'screenshots': ['asyncio_screenshot.png'],
            'research_complete': True
        }

    # Generate report
    print(f"\n" + "-"*70)
    print("Generating Report")
    print("-"*70)

    generator = ReportGenerator()
    report_path = await generator.generate_report(research_results)

    print(f"\n✓ Report generated: {report_path}")

    # Read and analyze report
    with open(report_path, 'r') as f:
        report_content = f.read()

    # Display preview
    print(f"\n" + "-"*70)
    print("Report Preview")
    print("-"*70)
    print(report_content[:1500])
    print("\n... (truncated)\n")

    # Validate report structure
    print("-"*70)
    print("Report Validation")
    print("-"*70)

    required_sections = {
        "# Deep Research Report:": "Title",
        "**Generated**:": "Metadata",
        "## Executive Summary": "Executive Summary",
        "## Key Findings": "Key Findings",
        "## Detailed Page Analysis": "Page Analysis",
        "## Resources Collected": "Resources",
        "## All Pages Visited": "Citations",
        "## Research Methodology": "Methodology"
    }

    validations = []

    for section, description in required_sections.items():
        if section in report_content:
            print(f"✓ Found: {description}")
            validations.append(True)
        else:
            print(f"✗ Missing: {description}")
            validations.append(False)

    # Additional checks
    print(f"\n--- Additional Checks ---")

    # Check metadata
    has_metadata = all(key in report_content for key in
                       ["**Base URL**:", "**Pages Explored**:", "**Estimated Relevance**:"])
    if has_metadata:
        print("✓ Metadata complete")
        validations.append(True)
    else:
        print("✗ Metadata incomplete")
        validations.append(False)

    # Check content not empty
    if len(report_content) > 1000:
        print(f"✓ Report size: {len(report_content)} characters")
        validations.append(True)
    else:
        print(f"✗ Report too short: {len(report_content)} characters")
        validations.append(False)

    # Check markdown formatting
    if "**URL**:" in report_content and "```" in report_content:
        print("✓ Markdown formatting present")
        validations.append(True)
    else:
        print("✗ Markdown formatting incomplete")
        validations.append(False)

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    all_passed = all(validations)
    status = "PASSED" if all_passed else "FAILED"
    status_icon = "✓" if all_passed else "✗"

    print(f"\n{status_icon} Test {status}")
    print(f"  Validations: {sum(validations)}/{len(validations)} passed")
    print(f"  Report size: {len(report_content)} characters")
    print(f"  Report location: {report_path}")

    print("\n" + "="*70 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(test_report_generation())
    sys.exit(0 if success else 1)
