# LLM Agent with Playwright MCP Server + Downloads & Screenshots

A learning project that demonstrates how to build an LLM agent that can control a web browser through natural language commands, **download files** (PDFs, Excel, CSV, etc.), and **save screenshots** to your local machine.

## Architecture

```
User Input (natural language)
    ↓
Python LLM Agent (agent.py)
    ↓ Uses OpenAI GPT-4
    ↓ Decides which tools to use
    ↓
MCP Client (Python SDK)
    ↓ stdio communication
    ↓
Microsoft Playwright MCP Server
    ↓
Web Browser (Chromium)
```

## What It Does

The agent can:
- 🌐 **Navigate** to websites
- 🔍 **Search** for content on pages
- 📥 **Download files** - PDFs, Excel, CSV, any file type (saved to disk!)
- 📸 **Save screenshots** - Capture pages as PNG images (saved to downloads/)
- ⌨️ **Fill forms** and click buttons
- 🤖 **Multi-step workflows** - combines actions intelligently

## Setup

### 1. Install Dependencies

**Python environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**Node.js** (for Playwright MCP server):
```bash
# Already available via npx, no installation needed
npx @playwright/mcp --version
```

### 2. Configure OpenAI API Key

Edit `.env` file and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o
```

Get your API key at: https://platform.openai.com/api-keys

## Usage

### Run the Agent

```bash
source .venv/bin/activate
python3 agent.py
```

### Example Commands

**Simple navigation:**
```
Navigate to https://www.irs.gov/forms-instructions
```

**Search and download:**
```
Search for W-4 form and download the PDF
```

**Multi-step workflow:**
```
Go to the IRS website, search for retirement tax forms, and download any PDFs you find
```

**Take screenshot:**
```
Take a screenshot of the current page
```

## How It Works

### 1. MCP Server Connection
The agent connects to Microsoft's Playwright MCP server via stdio (standard input/output):
- Launches: `npx @playwright/mcp`
- Discovers available tools automatically
- Tools include: navigate, click, fill, screenshot, etc.

### 2. OpenAI Function Calling
The agent uses OpenAI's function calling feature:
- Converts MCP tools to OpenAI function format
- Sends your natural language request to GPT-4
- GPT-4 decides which tools to call and with what parameters
- Handles multi-step workflows automatically

### 3. Tool Execution
When GPT-4 decides to use a tool:
- Agent sends tool request to MCP server
- MCP server controls the browser via Playwright
- Result is sent back to GPT-4
- GPT-4 decides next step (more tools or final response)

## Project Structure

```
.
├── agent.py              # Main LLM agent script
├── requirements.txt      # Python dependencies
├── .env                  # Configuration (API keys)
├── downloads/           # Downloaded files go here
├── .venv/              # Python virtual environment
└── README.md           # This file
```

## Key Concepts to Learn

### Model Context Protocol (MCP)
- A standard for connecting AI agents to tools and data sources
- Server exposes tools via a standard API
- Client (our agent) connects and calls tools
- stdio transport = communication via standard input/output

### OpenAI Function Calling
- GPT models can "call functions" based on natural language
- You provide function schemas (name, description, parameters)
- Model decides when and how to call functions
- Agent executes the actual function calls

### Multi-Step Workflows
- GPT can chain multiple tool calls together
- Example: navigate → search → analyze results → download
- Agent handles the loop automatically
- Stops when task is complete

## Test Websites

Good sites for testing (have PDFs and Excel files):

- **IRS Forms**: https://www.irs.gov/forms-instructions
- **SEC Edgar**: https://www.sec.gov/edgar/search/
- **Data.gov**: https://data.gov/

## Troubleshooting

**"OPENAI_API_KEY not found"**
- Make sure you created the `.env` file
- Add your API key: `OPENAI_API_KEY=sk-...`

**"Browser launch failed"**
- Playwright needs to download browser first
- Run: `npx playwright install chromium`

**"Module not found"**
- Make sure virtual environment is activated
- Run: `source .venv/bin/activate`
- Reinstall: `pip install -r requirements.txt`

## Next Steps

To extend this project:
- [ ] Add support for more file types (CSV, JSON, etc.)
- [ ] Implement session persistence (save browser state)
- [ ] Add vision capabilities (analyze screenshots with GPT-4 Vision)
- [ ] Create custom MCP server with domain-specific tools
- [ ] Add error recovery and retry logic
- [ ] Support multiple browser tabs

## Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [Playwright MCP Server](https://github.com/microsoft/playwright-mcp)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
