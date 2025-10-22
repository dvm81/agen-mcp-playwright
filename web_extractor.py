#!/usr/bin/env python3
"""
Web Content Extractor using Playwright MCP

This module extracts clean, readable content from webpages using
the Playwright MCP server's tools. It handles large pages intelligently
by using snapshots and selective content extraction.
"""

import asyncio
import re
from typing import Dict, Any, Optional
from mcp import ClientSession


class WebContentExtractor:
    """Extract clean content from webpages using Playwright MCP tools"""

    def __init__(self, mcp_session: ClientSession):
        self.session = mcp_session
        self.max_content_length = 15000  # ~4000 tokens

    async def extract_content(self, url: str) -> Dict[str, Any]:
        """
        Extract clean content from a URL.

        Returns:
            {
                'title': str,
                'content': str,  # Clean text content
                'url': str,
                'length': int,
                'method': str    # 'snapshot' or 'javascript'
            }
        """
        print(f"\n📄 Extracting content from: {url}")

        try:
            # Step 1: Navigate to the page
            await self.session.call_tool("browser_navigate", {"url": url})

            # Step 2: Try snapshot first (cleanest method)
            snapshot_result = await self.session.call_tool("browser_snapshot", {})

            snapshot_content = self._extract_from_snapshot(snapshot_result)

            if snapshot_content and len(snapshot_content) < self.max_content_length:
                print(f"✅ Extracted via snapshot ({len(snapshot_content)} chars)")
                return {
                    'title': await self._get_page_title(),
                    'content': snapshot_content,
                    'url': url,
                    'length': len(snapshot_content),
                    'method': 'snapshot'
                }

            # Step 3: If snapshot too large, use JavaScript extraction
            print("⚠️  Snapshot too large, using JavaScript extraction...")
            js_content = await self._extract_via_javascript()

            print(f"✅ Extracted via JavaScript ({len(js_content['content'])} chars)")
            return {
                **js_content,
                'url': url,
                'method': 'javascript'
            }

        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return {
                'title': 'Error',
                'content': f"Failed to extract content: {str(e)}",
                'url': url,
                'length': 0,
                'method': 'error'
            }

    def _extract_from_snapshot(self, snapshot_result) -> str:
        """Extract text content from Playwright snapshot"""
        try:
            content_text = ""

            for item in snapshot_result.content:
                if hasattr(item, 'text'):
                    # The snapshot returns YAML-like structured content
                    text = item.text

                    # Extract content from the "Page Snapshot" section
                    if "Page Snapshot:" in text:
                        # Get everything after the snapshot marker
                        parts = text.split("Page Snapshot:")
                        if len(parts) > 1:
                            snapshot_yaml = parts[1]
                            # Convert YAML structure to readable text
                            content_text = self._yaml_to_text(snapshot_yaml)
                    else:
                        content_text = text

            # Clean up the extracted text
            content_text = self._clean_text(content_text)

            return content_text[:self.max_content_length]

        except Exception as e:
            print(f"⚠️  Snapshot extraction failed: {e}")
            return ""

    def _yaml_to_text(self, yaml_content: str) -> str:
        """Convert YAML snapshot to readable text"""
        # Remove YAML formatting markers
        text = re.sub(r'```yaml\n', '', yaml_content)
        text = re.sub(r'```', '', text)

        # Extract text between quotes (actual content)
        # Pattern: "Some text content"
        quoted_text = re.findall(r'"([^"]+)"', text)

        # Extract text from various YAML patterns
        # Pattern: text: Something or heading "Something"
        labeled_text = re.findall(r'(?:text|heading|paragraph|link):\s*([^\n]+)', text)

        # Combine all extracted text
        all_text = quoted_text + labeled_text

        # Join with spaces and clean
        combined = ' '.join(all_text)

        return self._clean_text(combined)

    async def _extract_via_javascript(self) -> Dict[str, str]:
        """Extract main content using JavaScript in the browser"""
        extraction_js = """
        (() => {
            // Remove noise elements
            const removeSelectors = [
                'nav', 'footer', 'aside', 'header',
                '[role="navigation"]', '[role="banner"]',
                '.advertisement', '.ad', '.popup', '.modal',
                'script', 'style', 'iframe'
            ];

            removeSelectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(el => el.remove());
            });

            // Try to find main content area
            const mainContent =
                document.querySelector('main') ||
                document.querySelector('article') ||
                document.querySelector('[role="main"]') ||
                document.querySelector('.content') ||
                document.querySelector('#content') ||
                document.body;

            // Get all text content
            const text = mainContent.innerText || mainContent.textContent;

            // Clean up whitespace
            const cleaned = text
                .replace(/\\s+/g, ' ')
                .replace(/\\n\\s*\\n/g, '\\n')
                .trim();

            return {
                title: document.title,
                content: cleaned.slice(0, 15000),  // Limit to 15k chars
                length: cleaned.length
            };
        })()
        """

        result = await self.session.call_tool("browser_evaluate", {
            "expression": extraction_js
        })

        # Extract result from MCP response
        for item in result.content:
            if hasattr(item, 'text'):
                # The result is usually in the text as JSON-like format
                text = item.text
                # Try to parse the returned object
                # It might be in format: "### Result\n{title: ..., content: ...}"
                try:
                    # Look for the actual content after "Result" marker
                    if "Result" in text:
                        parts = text.split("Result")
                        if len(parts) > 1:
                            result_text = parts[1].strip()
                            # Extract content using regex
                            title_match = re.search(r'title:\s*"?([^",\n}]+)"?', result_text)
                            content_match = re.search(r'content:\s*"?([^"]+)"?', result_text, re.DOTALL)

                            return {
                                'title': title_match.group(1) if title_match else 'Unknown',
                                'content': self._clean_text(content_match.group(1) if content_match else text),
                                'length': len(content_match.group(1)) if content_match else len(text)
                            }
                except:
                    pass

                # Fallback: just return the text
                return {
                    'title': await self._get_page_title(),
                    'content': self._clean_text(text),
                    'length': len(text)
                }

        return {
            'title': 'Unknown',
            'content': 'No content extracted',
            'length': 0
        }

    async def _get_page_title(self) -> str:
        """Get the page title"""
        try:
            result = await self.session.call_tool("browser_evaluate", {
                "expression": "document.title"
            })

            for item in result.content:
                if hasattr(item, 'text'):
                    # Extract title from result text
                    text = item.text
                    if "Result" in text:
                        title = text.split("Result")[-1].strip()
                        return title.strip('"\'')
                    return text.strip('"\'')

            return "Unknown Title"
        except:
            return "Unknown Title"

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove common noise patterns
        text = re.sub(r'Cookie\s+Policy.*?Accept', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Subscribe\s+to\s+newsletter', '', text, flags=re.IGNORECASE)

        # Remove URLs (keep domain but remove full URLs)
        text = re.sub(r'https?://[^\s]+', '', text)

        # Normalize line breaks
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

        # Trim
        text = text.strip()

        return text

    async def extract_links(self, url: str, max_links: int = 10) -> list:
        """
        Extract relevant links from a page.
        Useful for finding related resources.
        """
        print(f"\n🔗 Extracting links from: {url}")

        try:
            await self.session.call_tool("browser_navigate", {"url": url})

            links_js = f"""
            (() => {{
                const links = Array.from(document.querySelectorAll('a'))
                    .filter(a => a.href && a.innerText)
                    .filter(a => !a.href.includes('javascript:'))
                    .filter(a => !a.href.includes('mailto:'))
                    .slice(0, {max_links})
                    .map(a => ({{
                        text: a.innerText.trim(),
                        url: a.href
                    }}));

                return links;
            }})()
            """

            result = await self.session.call_tool("browser_evaluate", {
                "expression": links_js
            })

            # Parse links from result
            links = []
            for item in result.content:
                if hasattr(item, 'text'):
                    # Extract link data
                    text = item.text
                    # This is simplified - you may need to parse the result better
                    print(f"✅ Found links in result")

            return links

        except Exception as e:
            print(f"❌ Error extracting links: {e}")
            return []


async def test_extractor():
    """Test the web content extractor"""
    from mcp import StdioServerParameters
    from mcp.client.stdio import stdio_client

    print("="*70)
    print("🧪 Testing Web Content Extractor")
    print("="*70)

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@playwright/mcp@latest"],
        env=None
    )

    async with stdio_client(server_params) as (stdio, write):
        async with ClientSession(stdio, write) as session:
            await session.initialize()

            extractor = WebContentExtractor(session)

            # Test with a few different sites
            test_urls = [
                "https://example.com",
                "https://en.wikipedia.org/wiki/Artificial_intelligence",
            ]

            for url in test_urls:
                print(f"\n{'='*70}")
                result = await extractor.extract_content(url)

                print(f"\n📊 Results:")
                print(f"  Title: {result['title']}")
                print(f"  Method: {result['method']}")
                print(f"  Length: {result['length']} characters")
                print(f"  Content preview: {result['content'][:200]}...")


if __name__ == "__main__":
    asyncio.run(test_extractor())
