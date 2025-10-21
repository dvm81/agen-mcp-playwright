#!/usr/bin/env python3
"""
Excel Download Demo

Test downloading an Excel file from a website.
We'll use a government data source that has Excel files.
"""

import asyncio
import json
import os
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")


def download_file(url: str, filename: str = None) -> str:
    """Download a file using Python requests"""
    downloads_dir = Path("downloads")
    downloads_dir.mkdir(exist_ok=True)

    if not filename:
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)

    filepath = downloads_dir / filename

    print(f"\n📥 Downloading from: {url}")
    print(f"   Saving as: {filename}")

    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size = os.path.getsize(filepath)
    print(f"✅ Downloaded successfully! Size: {file_size:,} bytes")
    print(f"   Location: {filepath.absolute()}")

    return f"Successfully downloaded {filename} ({file_size:,} bytes) to {filepath}"


async def demo_excel():
    print("="*70)
    print("📊 Excel File Download Demo")
    print("="*70)

    # Direct test with a known Excel file URL
    # IRS Publication 15-B contains Excel worksheets
    excel_url = "https://www.irs.gov/pub/irs-pdf/p15b.pdf"  # This is actually a PDF

    # Let's use a direct Excel file from IRS
    # Form 8962 has an Excel version
    print("\n📝 Note: We'll download a direct Excel file")
    print("   Using IRS Form 8962 Premium Tax Credit worksheet")

    # This is a known Excel file from IRS
    excel_url = "https://www.irs.gov/pub/irs-utl/8962-shared-policy-allocation-wks.xlsx"

    print(f"\n🔗 Direct URL: {excel_url}")

    result = download_file(excel_url, "IRS_Form_8962_Worksheet.xlsx")

    print(f"\n✅ {result}")

    print("\n" + "="*70)
    print("🎉 Excel Download Complete!")
    print("="*70)

    # List all downloaded files
    downloads_dir = Path("downloads")
    if downloads_dir.exists():
        files = list(downloads_dir.glob("*"))
        if files:
            print("\n📂 All downloaded files:")
            for f in files:
                size = f.stat().st_size
                file_type = f.suffix.upper()[1:] if f.suffix else "unknown"
                print(f"  - {f.name} ({file_type}, {size:,} bytes)")


if __name__ == "__main__":
    asyncio.run(demo_excel())
