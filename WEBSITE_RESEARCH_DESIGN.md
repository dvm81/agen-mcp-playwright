# Website Deep Research Agent - Design Document

## Overview

A deep research agent that thoroughly explores a **single website** to extract comprehensive information about a specific topic.

**No web search needed** - focuses on in-depth exploration of one authoritative source.

## Use Cases

Perfect for:
- 📚 **Documentation sites** - "Research FastAPI's async capabilities from fastapi.tiangolo.com"
- 🏢 **Company sites** - "Learn about Tesla's battery technology from tesla.com"
- 📰 **News sites** - "Research recent AI developments from techcrunch.com"
- 🎓 **Educational sites** - "Study machine learning from course.fast.ai"
- 📊 **Data sites** - "Explore climate data from data.gov"

## Architecture

### Phase 1: Scoping (Break Down the Website)

**Input**: URL + Research Topic

**Process**:
1. Navigate to homepage
2. Extract site structure (navigation, main sections)
3. LLM analyzes: which sections are relevant to topic?
4. Generate exploration plan (list of URLs to visit)

**Output**: Exploration plan
```python
{
    "base_url": "https://langchain.com",
    "topic": "Building agents with LangGraph",
    "pages_to_explore": [
        {"url": "/docs/concepts/agents", "priority": "high", "reason": "Core concepts"},
        {"url": "/docs/tutorials/langgraph", "priority": "high", "reason": "Practical tutorial"},
        {"url": "/docs/api/langgraph", "priority": "medium", "reason": "API reference"}
    ],
    "max_depth": 2  # How many link-hops from main pages
}
```

### Phase 2: Exploration (LangGraph State Machine)

**State**:
```python
class ExplorationState(TypedDict):
    current_url: str
    visited_urls: list[str]
    content_collected: list[dict]  # {url, title, content, links_found}
    downloads: list[str]  # Downloaded files
    screenshots: list[str]  # Screenshot paths
    depth: int  # Current exploration depth
    should_continue: bool  # Keep exploring?
```

**Nodes**:
1. **navigate** - Go to next URL in queue
2. **extract** - Get content with web_extractor
3. **analyze** - LLM decides: relevant? explore deeper?
4. **discover_links** - Find related pages to visit
5. **collect** - Download files, take screenshots
6. **decide_next** - Continue or finish?

**Graph Flow**:
```
navigate → extract → analyze
              ↓
         collect (if relevant)
              ↓
         discover_links
              ↓
         decide_next → [navigate again OR finish]
```

### Phase 3: Synthesis (Generate Report)

**Input**: All collected content

**Process**:
1. Group content by topic/section
2. LLM synthesizes key findings
3. Include citations (which page each fact came from)
4. List downloaded files and screenshots
5. Generate markdown report

**Output**: Comprehensive report
```markdown
# Deep Research: [Topic] from [Website]

Generated: 2024-01-20
Pages Explored: 15
Files Downloaded: 3
Screenshots: 7

## Executive Summary
[LLM-generated overview of all findings]

## Main Findings

### 1. [Topic Area 1]
[Synthesized content from relevant pages]

**Source**: [page URL]

### 2. [Topic Area 2]
...

## Resources Collected
- 📄 document1.pdf
- 📸 diagram_screenshot.png
- 📊 data_table.xlsx

## All Pages Visited
1. [URL] - [Title]
2. ...
```

## Implementation Plan

### Files to Create

1. **`website_scoper.py`** - Scope the website
   ```python
   class WebsiteScoper:
       async def scope(self, url, topic) -> ExplorationPlan
   ```

2. **`website_explorer.py`** - LangGraph exploration workflow
   ```python
   def create_exploration_graph() -> CompiledGraph
   ```

3. **`research_synthesizer.py`** - Generate final report
   ```python
   class ResearchSynthesizer:
       def generate_report(self, collected_content) -> str
   ```

4. **`deep_website_research.py`** - Main orchestrator
   ```python
   class DeepWebsiteResearcher:
       async def research(self, url, topic, max_pages=20)
   ```

### Dependencies

```python
# Already have:
- openai
- mcp (Playwright)
- requests

# Need to add:
- langgraph  # State machine workflow
- langchain-core  # Utilities
- langchain-openai  # OpenAI integration
```

### Smart Exploration Features

**Link Prioritization**:
- Analyze link text: "Getting Started" > "Privacy Policy"
- Check URL patterns: `/docs/` > `/blog/` > `/about/`
- LLM decides relevance to research topic

**Depth Control**:
```python
Max pages: 20  # Don't visit more than 20 pages
Max depth: 2   # Don't go more than 2 clicks from start
Time limit: 5 min  # Stop after time limit
```

**Smart Deduplication**:
- Don't visit same URL twice
- Skip irrelevant sections (footer links, etc.)
- Avoid infinite loops in site navigation

**Content Quality**:
- Only collect substantial content (>100 words)
- Prioritize pages with unique information
- Skip login/paywall pages

## Example Workflows

### Example 1: Documentation Research

```python
researcher = DeepWebsiteResearcher()

report = await researcher.research(
    url="https://docs.python.org",
    topic="asyncio and concurrent programming",
    max_pages=15
)

# Explores:
# - /library/asyncio.html
# - /library/concurrent.futures.html
# - /howto/async.html
# - Downloads: asyncio examples
# - Screenshots: asyncio workflow diagrams
```

### Example 2: Product Research

```python
report = await researcher.research(
    url="https://openai.com",
    topic="GPT-4 capabilities and pricing",
    max_pages=10
)

# Explores:
# - /gpt-4
# - /pricing
# - /api/documentation
# - Screenshots: pricing tables
# - Downloads: API docs PDF
```

### Example 3: News Research

```python
report = await researcher.research(
    url="https://techcrunch.com",
    topic="recent AI startup funding",
    max_pages=20
)

# Explores recent articles about AI funding
# Groups by company/topic
# Synthesizes trends
```

## Advantages Over Search-Based Research

✅ **Depth** - Explores interconnected pages, not just top results
✅ **Authority** - Focuses on one authoritative source
✅ **Context** - Understands site structure and relationships
✅ **Completeness** - Can find content buried deep in site
✅ **Files** - Collects PDFs, data files from the site
✅ **Visual** - Screenshots of diagrams, charts

## Testing Plan

**Test Sites**:
1. **Small, well-structured**: https://example.com
2. **Documentation**: https://docs.python.org/3/library/
3. **Complex**: https://github.com/langchain-ai/langgraph

**Test Topics**:
1. "How does asyncio work?" on Python docs
2. "LangGraph state machines" on LangChain docs
3. "Project structure and examples" on LangGraph GitHub

**Success Criteria**:
- Visits 10-15 relevant pages
- Extracts clean content from each
- Downloads 2-3 relevant files
- Takes 3-5 screenshots
- Generates coherent report
- Completes in <5 minutes

## Next Steps

Ready to build this! We'll create:

**Phase 1** (Next):
1. Install LangGraph
2. Create `website_scoper.py` - initial planning
3. Test scoping on a simple site

**Phase 2**:
4. Build LangGraph exploration loop
5. Integrate web_extractor
6. Test multi-page exploration

**Phase 3**:
7. Add report generation
8. Test end-to-end workflow
9. Polish and optimize

**Let's start with Phase 1!**
