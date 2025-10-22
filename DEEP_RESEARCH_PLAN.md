# Deep Research Agent Implementation Plan

## Current Status ✅

### What We Have Built
1. **Browser Automation** - Playwright MCP integration
2. **File Downloads** - PDFs, Excel, CSV, etc.
3. **Screenshots** - Save webpage captures
4. **Web Content Extractor** - Extract clean text from large webpages ✨ NEW!

### Web Extractor Capabilities
- Uses `browser_snapshot` for clean content (15KB limit)
- Falls back to `browser_evaluate` with JavaScript for large pages
- Strips ads, navigation, footers automatically
- Returns clean text suitable for LLM processing

##

 Next Steps: Building the Deep Research Agent

### Architecture (Based on LangChain's Approach)

```
User Research Query
    ↓
┌─────────────────────────────────┐
│ 1. SCOPING AGENT                │
│ - Break topic into sub-questions│
│ - Create research plan           │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. RESEARCH AGENT (LangGraph)   │
│                                  │
│  State Machine:                  │
│  ┌──────────────┐               │
│  │ Plan         │──→ Generate   │
│  └──────────────┘    questions  │
│         ↓                        │
│  ┌──────────────┐               │
│  │ Research     │──→ For each   │
│  │              │    question:  │
│  │              │    - Search   │
│  │              │    - Browse   │
│  │              │    - Extract  │
│  └──────────────┘               │
│         ↓                        │
│  ┌──────────────┐               │
│  │ Synthesize   │──→ Write      │
│  │              │    findings   │
│  └──────────────┘               │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. REPORT GENERATOR             │
│ - Aggregate all findings        │
│ - Generate markdown report      │
│ - Include citations             │
└─────────────────────────────────┘
```

### Components to Build

#### 1. Scoping Agent (`scoping_agent.py`)
**Purpose**: Break research topic into focused sub-questions

**Input**: "Research the impact of AI agents on software development"

**Output**:
```python
{
    "topic": "Impact of AI agents on software development",
    "sub_questions": [
        "What AI agent tools are currently available for developers?",
        "What productivity improvements have been measured?",
        "How are companies adopting AI agents?",
        "What are developers saying about AI agents?",
        "What are the future trends?"
    ]
}
```

**Implementation**:
```python
class ScopingAgent:
    def __init__(self, llm):
        self.llm = llm

    async def scope_research(self, topic: str) -> dict:
        # Use LLM to break topic into 3-5 sub-questions
        # Return structured research plan
```

#### 2. Research Agent (`research_agent.py`)
**Purpose**: Conduct research for each sub-question using LangGraph

**LangGraph State Machine**:
```python
class ResearchState(TypedDict):
    question: str
    search_results: list
    browsed_pages: list
    findings: str
    citations: list

def create_research_graph():
    workflow = StateGraph(ResearchState)

    # Nodes
    workflow.add_node("search", search_node)        # Search web
    workflow.add_node("browse", browse_node)        # Visit pages
    workflow.add_node("extract", extract_node)      # Extract content
    workflow.add_node("synthesize", synthesize_node)# Write findings

    # Edges
    workflow.add_edge("search", "browse")
    workflow.add_edge("browse", "extract")
    workflow.add_edge("extract", "synthesize")

    return workflow.compile()
```

**Tools Used**:
- `tavily_search` - Web search for URLs
- `web_extractor.extract_content()` - Get clean page content
- `download_file()` - Download PDFs/data
- `save_screenshot()` - Visual evidence

#### 3. Report Generator (`report_generator.py`)
**Purpose**: Create final research report

**Input**: All findings from sub-questions

**Output**: Markdown report
```markdown
# Research Report: Impact of AI Agents on Software Development

## Executive Summary
[Generated summary]

## 1. Current AI Agent Tools
[Findings from sub-question 1]

### Sources
- [1] GitHub Copilot Documentation
- [2] ...

## 2. Productivity Improvements
[Findings from sub-question 2]

...
```

### Dependencies Needed

```txt
# Already have:
openai>=1.0.0
mcp>=0.1.0
requests>=2.31.0

# Need to add:
langgraph>=0.2.0          # State machine workflow
langchain-core>=0.3.0     # Agent utilities
langchain-openai>=0.2.0   # OpenAI integration
tavily-python>=0.5.0      # Web search API
```

### File Structure

```
mcp/
├── agent.py                    # Original interactive agent
├── web_extractor.py           # ✅ NEW: Extract clean content
├── scoping_agent.py           # TODO: Break topics into questions
├── research_agent.py          # TODO: LangGraph research workflow
├── report_generator.py        # TODO: Generate final reports
├── deep_research.py          # TODO: Main orchestrator
└── research_outputs/         # TODO: Store reports
```

### Implementation Steps

**Phase 1: Core Setup** (Next)
1. Install LangGraph dependencies
2. Create basic scoping agent
3. Test topic → sub-questions workflow

**Phase 2: Research Loop**
4. Build LangGraph state machine
5. Integrate web_extractor
6. Add search capability (Tavily)
7. Test single sub-question research

**Phase 3: Full Workflow**
8. Connect scoping → research → report
9. Test end-to-end with real topic
10. Save reports as markdown files

**Phase 4: Polish**
11. Add progress tracking
12. Error handling and retries
13. Citation management
14. Multi-format exports (MD, PDF)

### Example Usage (Goal)

```python
from deep_research import DeepResearchAgent

agent = DeepResearchAgent()

# Simple API
report = await agent.research(
    topic="Impact of AI agents on software development in 2024",
    depth=5  # Number of sub-questions
)

# report.md saved to research_outputs/
# Contains: findings, citations, screenshots, downloaded PDFs
```

### Advantages Over Standard Research Agents

Your agent will have unique capabilities:

1. **Real Browsing** - Not just search results, actual page interaction
2. **File Collection** - Download PDFs, data files for evidence
3. **Visual Documentation** - Screenshots of key findings
4. **Form Access** - Can access gated content
5. **MCP Extensibility** - Can add any MCP server tools

### Testing Plan

**Test Topics**:
1. "How do LLM agents work?" (Simple, well-documented)
2. "Latest developments in battery technology 2024" (Current events)
3. "Comparison of web scraping tools" (Technical, multiple sources)

Each test should produce:
- Markdown report
- Downloaded PDFs (if relevant)
- Screenshots of key pages
- Cited sources

---

## Ready to Continue?

The web extractor is working! Now we can:

**Option A**: Install LangGraph and build the scoping agent
**Option B**: Test web_extractor more thoroughly first
**Option C**: Build a simple research loop without LangGraph first (simpler)

Which would you prefer?
