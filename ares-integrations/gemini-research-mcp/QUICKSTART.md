# Quick Start Guide

Get your Gemini Research MCP server running in 5 minutes.

## Prerequisites

- Node.js 18+ installed
- Claude Code installed
- Gemini API key (free at https://aistudio.google.com/apikey)

## Step 1: Install

```bash
cd C:\Users\riord\gemini-research-mcp
npm install
```

## Step 2: Configure API Key

Create `.env` file:
```bash
cp .env.example .env
```

Edit `.env` and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_key_here
```

## Step 3: Build

```bash
npm run build
```

## Step 4: Configure Claude Code

Edit your Claude Code config file:
- **Windows**: `%APPDATA%\Claude Code\claude_desktop_config.json`
- **Mac**: `~/Library/Application Support/Claude Code/claude_desktop_config.json`

Add this (update the path if different):

```json
{
  "mcpServers": {
    "gemini-research": {
      "command": "node",
      "args": ["C:\\Users\\riord\\gemini-research-mcp\\dist\\index.js"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here"
      }
    }
  }
}
```

## Step 5: Restart Claude Code

Restart Claude Code completely (quit and reopen).

## Step 6: Test It

In Claude Code, try:

```
Use deep_research to analyze "best Python web framework for APIs" with focus on ["performance", "ease of use", "community support"]
```

You should see results from Google Scholar, YouTube, and Gemini analysis!

## Common Issues

**"Tool not found"**: Restart Claude Code after config changes

**"Gemini API error"**: Check your API key in `.env` and config file

**"No results"**: Some searches may be rate-limited; try simpler queries first

## Next Steps

- Read the full [README.md](README.md) for all features
- Try the `weighted_decision` tool for architectural choices
- Explore the `scholar_search` and `youtube_research` tools
- Add optional YouTube API key for better video results

## Example Queries

### Technology Decisions
```
Use weighted_decision for "Should I use REST or GraphQL?" with criteria ["performance", "developer experience", "tooling"] and context "building a mobile app backend"
```

### Learning
```
Use youtube_research to find tutorials on "Docker containerization best practices"
```

### Academic Research
```
Use scholar_search to find papers about "transformer architecture optimization"
```

### Deep Analysis
```
Use gemini_query with "Compare microservices vs serverless architecture for a startup. Include cost analysis, scalability, and operational complexity."
```

Enjoy your research superpower!
