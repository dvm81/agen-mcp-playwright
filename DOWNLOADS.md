# File Downloads - Explanation and Solutions

## Why the Agent Can't Download Files (Currently)

### The Problem

When you ask the agent to "download a PDF", here's what actually happens:

1. ✅ Agent navigates to the IRS forms page
2. ✅ Agent clicks the PDF link (e.g., Form W-4)
3. ✅ Browser navigates to the PDF URL: `https://www.irs.gov/pub/irs-pdf/fw4.pdf`
4. ❌ **But the file is NOT saved to your disk**

The PDF opens in the browser tab, but it's not downloaded to the `downloads/` folder.

### Why This Happens

The **Microsoft Playwright MCP server** provides 21 browser automation tools, but **none of them directly handle file downloads to disk**. The available tools are:

- `browser_navigate` - Opens URLs
- `browser_click` - Clicks links
- `browser_evaluate` - Runs JavaScript
- `browser_take_screenshot` - Saves screenshots
- etc.

But there's **no `browser_download` tool**.

### What the MCP Server CAN Do

The server can:
- Navigate to the PDF URL ✅
- Display the PDF in the browser ✅
- Run JavaScript to fetch the file content ✅
- Take screenshots of pages ✅

The server **cannot** (without custom code):
- Save files to your local filesystem ❌
- Handle browser download events ❌
- Write binary files to disk ❌

## Solutions

### Solution 1: Use Python to Download Files Directly

Instead of having Playwright download files, use Python's `requests` library:

```python
import requests

async def download_file(url, filename):
    """Download a file directly using Python"""
    response = requests.get(url)
    with open(f"downloads/{filename}", "wb") as f:
        f.write(response.content)
    print(f"✅ Downloaded: {filename}")

# Usage in your agent:
# 1. Use LLM to find the PDF URL
# 2. Extract the URL from the result
# 3. Download using Python directly
```

**Pros**: Simple, reliable, works with any file type
**Cons**: Requires knowing the direct URL

### Solution 2: Enhanced Agent with Download Tool

Create a custom tool that combines navigation + download:

```python
async def download_from_link(session, link_text):
    """
    1. Click the link
    2. Get the resulting URL
    3. Use Python requests to download
    """
    # Click the link
    await session.call_tool("browser_click", {"element": link_text})

    # Get current URL (the PDF/file URL)
    result = await session.call_tool("browser_evaluate",
                                     {"expression": "window.location.href"})
    file_url = extract_url(result)

    # Download using Python
    filename = file_url.split('/')[-1]
    response = requests.get(file_url)

    with open(f"downloads/{filename}", "wb") as f:
        f.write(response.content)

    return f"Downloaded: {filename}"
```

### Solution 3: Custom MCP Server

Build your own MCP server that includes a download tool:

```javascript
// custom-playwright-server.js
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  if (request.params.name === "download_file") {
    const url = request.params.arguments.url;
    const filename = request.params.arguments.filename;

    // Use Playwright's download handling
    const downloadPromise = page.waitForEvent('download');
    await page.goto(url);
    const download = await downloadPromise;
    await download.saveAs(`./downloads/${filename}`);

    return { content: [{ type: "text", text: `Downloaded: ${filename}` }] };
  }
});
```

### Solution 4: Use `browser_evaluate` to Get File Content

Fetch the file in the browser and return it to Python:

```python
download_js = f"""
(async () => {{
    const response = await fetch('{pdf_url}');
    const blob = await response.blob();
    const arrayBuffer = await blob.arrayBuffer();
    const bytes = new Uint8Array(arrayBuffer);

    // Convert to base64
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {{
        binary += String.fromCharCode(bytes[i]);
    }}
    return btoa(binary);
}})()
"""

result = await session.call_tool("browser_evaluate", {"expression": download_js})
# Then decode base64 and save in Python
```

**Pros**: Uses only existing MCP tools
**Cons**: Size limits on base64 encoding, complex

## Recommended Approach for Learning

For your learning project, I recommend **Solution 1 + Solution 2** combined:

### Enhanced Agent Architecture

```
User: "Download Form W-4 PDF"
    ↓
LLM Agent decides strategy:
    1. Navigate to IRS forms page (browser_navigate)
    2. Find the W-4 link (browser_snapshot)
    3. Extract the PDF URL from link
    4. Download using Python requests ← NEW!
    5. Save to downloads/ folder
```

### Implementation

Add this to your agent:

```python
import requests

class PlaywrightAgent:
    # ... existing code ...

    async def download_file_from_url(self, url: str, filename: str = None):
        """Download a file using Python requests"""
        if not filename:
            filename = url.split('/')[-1]

        filepath = f"downloads/{filename}"

        print(f"📥 Downloading {url}")
        response = requests.get(url)

        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"✅ Saved to {filepath}")
        return filepath
```

Then expose this as a tool to the LLM:

```python
{
    "type": "function",
    "function": {
        "name": "download_file",
        "description": "Download a file from a URL to the downloads folder",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the file to download"
                },
                "filename": {
                    "type": "string",
                    "description": "Optional filename to save as"
                }
            },
            "required": ["url"]
        }
    }
}
```

## Summary

**Current State**:
- Agent can navigate and find files ✅
- Agent can click download links ✅
- Files open in browser but aren't saved ❌

**Why**:
- Playwright MCP server has no download-to-disk tool
- It's designed for browser testing, not file management

**Best Solution**:
- Use LLM to find the file URL
- Use Python `requests` to download
- Give the LLM a custom `download_file` tool

This hybrid approach:
- Leverages browser automation for navigation
- Uses Python for actual file I/O
- Gives you full control over downloads
- Works with any file type (PDF, Excel, CSV, etc.)

## Next Steps

Want me to implement the enhanced agent with actual download capability? I can:

1. Add `requests` to requirements.txt
2. Create a `download_file` function
3. Expose it as a tool to the LLM
4. Test with IRS forms (PDF) and other sites (Excel)

Let me know if you'd like me to build this!
