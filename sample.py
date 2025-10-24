#!/usr/bin/env python3
"""
Self-contained Playwright PDF downloader for corporate intranet
Requires: pip install playwright
Then run: playwright install chromium
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright

# ============ CONFIGURATION ============
DOWNLOAD_DIR = "./downloads"  # Change to your desired directory
INTRANET_URL = "https://intranet.company.com/document.pdf"  # Your hardcoded URL

# Certificate authentication (adjust paths)
CERT_PATH = "/path/to/client-cert.pem"  # Or .crt
KEY_PATH = "/path/to/client-key.pem"   # Or .key
# Or for .pfx format:
# PFX_PATH = "/path/to/cert.pfx"
# PFX_PASSWORD = "your-password"

# =======================================

async def download_pdf():
    """Download PDF from intranet site with certificate auth"""
    
    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    print(f"📁 Download directory: {os.path.abspath(DOWNLOAD_DIR)}")
    
    async with async_playwright() as p:
        # Launch Chromium
        browser = await p.chromium.launch(
            headless=False  # Set True for headless mode
        )
        
        # Create context with certificate authentication
        context = await browser.new_context(
            client_certificates=[{
                "origin": INTRANET_URL.split('/')[0] + '//' + INTRANET_URL.split('/')[2],
                "certPath": CERT_PATH,
                "keyPath": KEY_PATH,
                # For .pfx format, use instead:
                # "pfxPath": PFX_PATH,
                # "passphrase": PFX_PASSWORD
            }],
            accept_downloads=True,
            downloads_path=DOWNLOAD_DIR,
            ignore_https_errors=True  # If using internal CA
        )
        
        page = await context.new_page()
        
        print(f"🌐 Navigating to: {INTRANET_URL}")
        
        # Option A: Direct PDF download
        try:
            async with page.expect_download() as download_info:
                await page.goto(INTRANET_URL, wait_until="networkidle")
            
            download = await download_info.value
            filename = download.suggested_filename
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            
            await download.save_as(filepath)
            print(f"✅ Downloaded: {filename}")
            print(f"📍 Location: {os.path.abspath(filepath)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            
            # Option B: If it's a link to click instead
            print("Trying alternative method (looking for download link)...")
            try:
                async with page.expect_download() as download_info:
                    # Adjust selector to your specific download button/link
                    await page.click('a:has-text("Download")')  # Or use specific selector
                
                download = await download_info.value
                filename = download.suggested_filename
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                await download.save_as(filepath)
                print(f"✅ Downloaded: {filename}")
                print(f"📍 Location: {os.path.abspath(filepath)}")
            except Exception as e2:
                print(f"❌ Also failed: {e2}")
                # Take screenshot for debugging
                await page.screenshot(path=os.path.join(DOWNLOAD_DIR, "debug.png"))
                print(f"📸 Screenshot saved to: {DOWNLOAD_DIR}/debug.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_pdf())
