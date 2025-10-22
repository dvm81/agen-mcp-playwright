# Testing Guide: Deep Research Agent

This guide explains how to test the Deep Research Agent system both component-by-component and end-to-end.

## Table of Contents

- [Quick Start](#quick-start)
- [Component Tests](#component-tests)
- [End-to-End Tests](#end-to-end-tests)
- [What to Look For](#what-to-look-for)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Activate virtual environment
source .venv/bin/activate

# Run quick end-to-end test (recommended first test)
python3 tests/test_e2e_quick.py

# Or test individual components
python3 tests/test_extractor.py
```

---

## Component Tests

Test individual components in isolation. Run these bottom-up to verify each piece works before testing the full system.

### 1. Web Content Extractor

**File:** `tests/test_extractor.py`
**Purpose:** Tests content extraction from webpages
**Duration:** ~30 seconds per URL

```bash
python3 tests/test_extractor.py
```

**What it tests:**
- Clean content extraction from various website types
- Content length limits (max 15KB)
- Title extraction
- Extraction method (snapshot vs. JavaScript)
- Removal of navigation, ads, and clutter

**Success indicators:**
- ✓ Content extracted from all test URLs
- ✓ Content is clean and readable
- ✓ Length under 15KB (~4000 tokens)
- ✓ Title correctly extracted
- ✓ No Python exceptions

**Output:**
- Console output with extraction results
- Content previews (first 500 chars)

---

### 2. Website Scoper

**File:** `tests/test_scoper.py`
**Purpose:** Tests LLM-powered site analysis and planning
**Duration:** ~1 minute per site

```bash
python3 tests/test_scoper.py
```

**What it tests:**
- Website structure analysis
- Relevant page identification
- Page prioritization (HIGH/MEDIUM/LOW)
- Relevance scoring
- LLM reasoning quality

**Success indicators:**
- ✓ LLM identifies topic-relevant pages
- ✓ Pages prioritized correctly
- ✓ Number of pages ≤ max_pages parameter
- ✓ Estimated relevance > 50%
- ✓ Reasoning makes sense

**Output:**
- Console output with exploration plans
- JSON files saved to `tests/output/plan_*.json`

---

### 3. Research Agent

**File:** `tests/test_research_agent.py`
**Purpose:** Tests LangGraph workflow and state machine
**Duration:** ~2-3 minutes for 3 pages

```bash
python3 tests/test_research_agent.py
```

**What it tests:**
- LangGraph state transitions
- Page navigation
- Content collection
- LLM synthesis (value assessment, summaries, key points)
- Screenshot capture for HIGH priority pages

**Success indicators:**
- ✓ All planned pages visited
- ✓ Content extracted from each page
- ✓ LLM synthesis includes summaries and key points
- ✓ Screenshots saved for HIGH priority pages
- ✓ Research marked as complete

**Output:**
- Console output with workflow progress
- JSON file saved to `tests/output/research_results.json`

---

### 4. Report Generator

**File:** `tests/test_report_generator.py`
**Purpose:** Tests markdown report generation
**Duration:** ~10 seconds

```bash
python3 tests/test_report_generator.py
```

**What it tests:**
- Report structure (all required sections)
- Executive summary generation
- Findings organization (by value)
- Markdown formatting
- Citations and resources

**Success indicators:**
- ✓ All required sections present:
  - Executive Summary
  - Key Findings
  - Detailed Page Analysis
  - Resources Collected
  - All Pages Visited
  - Research Methodology
- ✓ Markdown formatting correct
- ✓ Report size > 1000 characters
- ✓ Metadata complete

**Output:**
- Console output with validation results
- Report saved to `research_outputs/`

---

## End-to-End Tests

Test the complete workflow from start to finish.

### Quick E2E Test (Recommended)

**File:** `tests/test_e2e_quick.py`
**Purpose:** Fast validation with small scope (3-4 pages)
**Duration:** ~2-4 minutes per test case

```bash
python3 tests/test_e2e_quick.py
```

**Test cases:**
1. FastAPI dependency injection (3 pages)
2. Python decorators (4 pages)

**What it tests:**
- Complete workflow: scoping → exploration → report
- All components working together
- Report quality with limited scope

**Success indicators:**
- ✓ Report generated for each test case
- ✓ All required sections present
- ✓ Pages documented
- ✓ No errors during execution

---

### Comprehensive E2E Test

**File:** `tests/test_e2e_full.py`
**Purpose:** Thorough validation with larger scope (8-12 pages)
**Duration:** ~5-10 minutes per test case

```bash
python3 tests/test_e2e_full.py
```

**Test cases:**
1. React hooks and lifecycle (10 pages)
2. LangChain chains and agents (12 pages)
3. Playwright browser automation (8 pages)

**What it tests:**
- System performance with larger scope
- Complex documentation sites
- Multiple topics and page types
- Full report quality

**Success indicators:**
- ✓ All test cases pass
- ✓ Reports comprehensive and well-formatted
- ✓ Pages documented ≥ 50% of max_pages
- ✓ Screenshots captured
- ✓ Executive summaries generated

---

## What to Look For

### Success Indicators

When tests pass, you should see:

- ✓ No Python errors or exceptions
- ✓ All pages visited successfully
- ✓ Content extracted (not empty)
- ✓ LLM synthesis includes:
  - Value assessment (yes/somewhat/no)
  - Summary (1-2 sentences)
  - Key points (3-5 bullet points)
  - Notable quotes (if relevant)
- ✓ Screenshots saved for HIGH priority pages
- ✓ Reports include executive summary
- ✓ Markdown formatting correct
- ✓ All required sections present

### Warning Signs

If you see these, investigate further:

- ✗ Empty content extractions
- ✗ Missing synthesis data
- ✗ No screenshots for HIGH priority pages
- ✗ Generic or repetitive LLM summaries
- ✗ Broken URLs in report
- ✗ Missing report sections
- ✗ Content over 15KB limit
- ✗ Low relevance scores (<50%)

---

## Test Output Files

Tests create output files for inspection:

```
tests/output/
├── plan_*.json              # Exploration plans from scoper tests
└── research_results.json    # Research data from agent tests

research_outputs/
└── research_report_*.md     # Generated reports
```

---

## Running All Tests

Run all tests sequentially:

```bash
# Activate environment
source .venv/bin/activate

# Component tests
echo "Running component tests..."
python3 tests/test_extractor.py
python3 tests/test_scoper.py
python3 tests/test_research_agent.py
python3 tests/test_report_generator.py

# End-to-end tests
echo "Running E2E tests..."
python3 tests/test_e2e_quick.py
python3 tests/test_e2e_full.py  # This takes 15-30 minutes
```

Or create a test runner:

```bash
cat > run_all_tests.sh << 'EOF'
#!/bin/bash
set -e

source .venv/bin/activate

echo "================================"
echo "Running Component Tests"
echo "================================"

python3 tests/test_extractor.py
python3 tests/test_scoper.py
python3 tests/test_research_agent.py
python3 tests/test_report_generator.py

echo ""
echo "================================"
echo "Running E2E Tests"
echo "================================"

python3 tests/test_e2e_quick.py

echo ""
echo "================================"
echo "All Tests Passed!"
echo "================================"
EOF

chmod +x run_all_tests.sh
./run_all_tests.sh
```

---

## Troubleshooting

### Common Issues

**1. MCP Connection Errors**

```
Error: Failed to connect to Playwright MCP server
```

**Solution:**
- Check `@playwright/mcp` is installed globally: `npm list -g @playwright/mcp`
- Verify `npx @playwright/mcp` runs without errors
- Check your `OPENAI_API_KEY` is set in `.env`

**2. Empty Content Extraction**

```
✗ Content is empty
```

**Solution:**
- Check internet connection
- Verify URL is accessible (not behind login/paywall)
- Try different extraction method (snapshot vs. JavaScript)
- Check if website blocks automation

**3. LLM Synthesis Missing**

```
✗ No LLM synthesis found
```

**Solution:**
- Verify OpenAI API key is valid
- Check API quota/rate limits
- Review `research_agent.py` synthesis prompts
- Check for API errors in console output

**4. Test Timeout**

```
Error: Test exceeded timeout
```

**Solution:**
- Reduce `max_pages` parameter for testing
- Check network latency
- Some websites are slow - this is expected
- Use `test_e2e_quick.py` instead of `test_e2e_full.py`

**5. Screenshots Not Saved**

```
✗ No screenshots for HIGH priority pages
```

**Solution:**
- Check `research_outputs/` directory exists
- Verify write permissions
- Check Playwright screenshot tool is working
- Review `agent.py` screenshot method

---

## Custom Test Scenarios

Create your own test:

```python
# tests/my_custom_test.py
import asyncio
from deep_research import DeepWebsiteResearcher

async def main():
    researcher = DeepWebsiteResearcher()

    report = await researcher.research(
        url="https://your-website.com",
        topic="your research topic",
        max_pages=5
    )

    print(f"Report generated: {report}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run it:

```bash
python3 tests/my_custom_test.py
```

---

## Test Development Tips

When writing new tests:

1. **Start small** - Test with 3-5 pages before scaling up
2. **Use real websites** - Test against actual documentation sites
3. **Check all outputs** - Verify console output AND generated files
4. **Save artifacts** - Keep JSON files and reports for debugging
5. **Test error cases** - Try invalid URLs, rate limits, etc.
6. **Time your tests** - Know how long each component takes
7. **Validate reports** - Don't just check they exist, read them!

---

## Continuous Testing

Set up automated testing:

```bash
# Add to your .git/hooks/pre-commit
#!/bin/bash
source .venv/bin/activate
python3 tests/test_extractor.py || exit 1
python3 tests/test_e2e_quick.py || exit 1
```

Or use a testing framework:

```bash
# Install pytest
pip install pytest pytest-asyncio

# Run all tests
pytest tests/
```

---

## Questions?

- Check the main [README.md](README.md) for architecture overview
- Review individual component files for implementation details
- See example reports in `research_outputs/`
- Check `DEEP_RESEARCH_PLAN.md` for design decisions

---

**Happy Testing! 🧪**
