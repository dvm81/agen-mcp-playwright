"""
Test script for web_extractor.py

Tests content extraction from webpages using Playwright MCP.
Verifies clean content extraction, title parsing, and length limits.
"""

import asyncio
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_extractor import WebContentExtractor


async def test_extraction():
    """Test extracting content from various webpages"""

    extractor = WebContentExtractor()

    try:
        # Test URLs - different types of websites
        test_urls = [
            "https://docs.python.org/3/library/asyncio.html",
            "https://en.wikipedia.org/wiki/Python_(programming_language)",
            "https://github.com/langchain-ai/langgraph"
        ]

        print("\n" + "="*70)
        print("WEB CONTENT EXTRACTOR TEST")
        print("="*70)

        results = []

        for i, url in enumerate(test_urls, 1):
            print(f"\n[Test {i}/{len(test_urls)}] Testing: {url}")
            print("-" * 70)

            try:
                result = await extractor.extract_content(url)

                print(f"✓ Title: {result.get('title', 'N/A')}")
                print(f"✓ URL: {result['url']}")
                print(f"✓ Content length: {len(result['content'])} characters")
                print(f"✓ Extraction method: {result['extraction_method']}")

                # Validate content
                assert len(result['content']) > 0, "Content is empty"
                assert len(result['content']) <= 15000, "Content exceeds 15KB limit"
                assert result['url'] == url, "URL mismatch"

                print(f"\n--- Content Preview (first 500 chars) ---")
                print(result['content'][:500])
                if len(result['content']) > 500:
                    print("...")

                results.append({
                    'url': url,
                    'status': 'PASSED',
                    'title': result.get('title', 'N/A'),
                    'content_length': len(result['content']),
                    'method': result['extraction_method']
                })

            except Exception as e:
                print(f"✗ FAILED: {e}")
                results.append({
                    'url': url,
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
            print(f"  URL: {result['url']}")

            if result['status'] == 'PASSED':
                print(f"  Title: {result['title']}")
                print(f"  Content: {result['content_length']} chars")
                print(f"  Method: {result['method']}")
            else:
                print(f"  Error: {result.get('error', 'Unknown')}")

        print("\n" + "="*70)
        print(f"Results: {passed}/{len(test_urls)} tests passed")
        print("="*70 + "\n")

        return passed == len(test_urls)

    finally:
        await extractor.close()


if __name__ == "__main__":
    success = asyncio.run(test_extraction())
    sys.exit(0 if success else 1)
