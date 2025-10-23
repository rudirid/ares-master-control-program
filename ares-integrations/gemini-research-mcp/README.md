# Gemini Research MCP Server

A powerful Model Context Protocol (MCP) server that integrates Claude with Google's Gemini API, Google Scholar, and YouTube for deep research and weighted decision-making in software and AI development projects.

## Features

- **Deep Research**: Comprehensive research combining academic papers, video tutorials, and AI analysis
- **Google Scholar Integration**: Search and analyze academic papers with credibility scoring
- **YouTube Research**: Find technical tutorials, talks, and demonstrations
- **Weighted Decision-Making**: AI-powered analysis with confidence scoring and evidence-based recommendations
- **Direct Gemini Access**: Query Gemini Pro model for complex analysis and synthesis

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
cd gemini-research-mcp
npm install
```

3. Create a `.env` file from the example:

```bash
cp .env.example .env
```

4. Add your API keys to `.env`:
   - Get a Gemini API key from: https://aistudio.google.com/apikey
   - (Optional) Get a YouTube API key from: https://console.cloud.google.com/apis/credentials

```env
GEMINI_API_KEY=your_actual_gemini_key_here
YOUTUBE_API_KEY=your_youtube_key_here  # Optional but recommended
```

5. Build the server:

```bash
npm run build
```

## Configuration for Claude Code

Add this MCP server to your Claude Code configuration file:

### Windows
Edit: `%APPDATA%\Claude Code\claude_desktop_config.json`

### macOS/Linux
Edit: `~/Library/Application Support/Claude Code/claude_desktop_config.json`

Add the following to the `mcpServers` section:

```json
{
  "mcpServers": {
    "gemini-research": {
      "command": "node",
      "args": ["C:\\Users\\riord\\gemini-research-mcp\\dist\\index.js"],
      "env": {
        "GEMINI_API_KEY": "your_gemini_api_key_here",
        "YOUTUBE_API_KEY": "your_youtube_api_key_here"
      }
    }
  }
}
```

**Important**: Replace the path with the actual absolute path to your installation, and add your actual API keys.

After updating the config, restart Claude Code.

## Available Tools

### 1. `deep_research`
Perform comprehensive research using all available sources.

**Parameters:**
- `query` (required): The research question
- `context` (optional): Additional project context
- `focus_areas` (optional): Array of specific focus areas (e.g., ["performance", "scalability"])

**Example:**
```
Use deep_research to analyze "best database for real-time analytics" with context "building a stock trading system" and focus on ["performance", "latency", "cost"]
```

### 2. `scholar_search`
Search Google Scholar for academic papers.

**Parameters:**
- `query` (required): Academic search query
- `max_results` (optional): Maximum results (default: 10)

**Example:**
```
Use scholar_search to find papers about "neural network optimization techniques"
```

### 3. `youtube_research`
Search YouTube for technical content.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Maximum results (default: 10)

**Example:**
```
Use youtube_research to find tutorials on "FastAPI microservices architecture"
```

### 4. `weighted_decision`
Get AI-powered decision recommendations with evidence.

**Parameters:**
- `question` (required): The decision question
- `criteria` (optional): Array of decision criteria
- `context` (optional): Project constraints and context

**Example:**
```
Use weighted_decision for "Should I use PostgreSQL or MongoDB?" with criteria ["query performance", "scalability", "developer experience"] and context "building a social media platform"
```

### 5. `gemini_query`
Direct access to Gemini Pro for custom analysis.

**Parameters:**
- `prompt` (required): Your prompt/question
- `temperature` (optional): Creativity level 0.0-1.0 (default: 0.7)

**Example:**
```
Use gemini_query with "Explain the trade-offs between microservices and monolithic architecture for a startup" at temperature 0.3
```

## Usage Examples

### Example 1: Technology Decision
```
Claude, I need to choose between React and Vue for my new project. Use the deep_research tool to analyze this decision with context "building a dashboard for financial data" and focus on ["performance", "ecosystem", "learning curve", "enterprise support"].
```

### Example 2: Architecture Research
```
Use scholar_search to find academic research on "event-driven architecture patterns" and then use weighted_decision to recommend whether I should use event sourcing for my e-commerce platform.
```

### Example 3: Learning Resources
```
I'm implementing OAuth 2.0. Use youtube_research to find the best tutorials and demonstrations on "OAuth 2.0 implementation in Node.js"
```

### Example 4: Technical Analysis
```
Use gemini_query to analyze: "What are the security implications of using JWT tokens vs session-based authentication in a microservices architecture? Provide specific attack vectors and mitigation strategies."
```

## How It Works

### Research Workflow
1. **Parallel Data Gathering**: Queries Google Scholar, YouTube, and Gemini simultaneously
2. **Credibility Scoring**: Assigns credibility scores (Academic: 0.9, Videos: 0.7)
3. **Relevance Ranking**: Ranks results based on position and engagement metrics
4. **AI Synthesis**: Gemini analyzes and synthesizes all findings
5. **Weighted Recommendations**: Provides confidence-scored recommendations with evidence

### Decision-Making Process
1. Gathers research from multiple sources
2. Evaluates against your specified criteria
3. Calculates confidence scores (0-100)
4. Provides clear recommendations with reasoning
5. Lists alternative options with trade-offs

## Technical Details

### Architecture
- **TypeScript**: Full type safety
- **MCP SDK**: Standard protocol for LLM integration
- **Gemini Pro**: Google's advanced AI model
- **Async Operations**: Parallel research for speed
- **Error Handling**: Graceful fallbacks and retries

### Credibility Weighting
- Academic papers (Scholar): 0.9
- Video tutorials (YouTube): 0.7
- AI analysis (Gemini): Context-dependent
- Combined with relevance scoring for final ranking

### Rate Limiting & Ethics
- Respects robots.txt
- Uses appropriate User-Agent headers
- Includes timeouts (default: 60s)
- Falls back gracefully on errors

## Troubleshooting

### "Gemini API error"
- Verify your API key in `.env`
- Check you have credits at https://aistudio.google.com/
- Ensure you're not hitting rate limits

### "No results from Scholar"
- Google Scholar may be rate-limiting
- Try reducing `max_results`
- Add delays between requests

### "YouTube search returns empty"
- Without YouTube API key, scraping is less reliable
- Add a proper API key for better results
- Some queries may not return results due to YouTube's changing HTML

### Server not appearing in Claude
- Restart Claude Code after config changes
- Check the absolute path in your config
- Verify the build succeeded (`npm run build`)
- Check Claude Code logs for errors

## Development

### Building
```bash
npm run build
```

### Watch Mode
```bash
npm run dev
```

### Testing Locally
```bash
# After building
node dist/index.js
```

The server communicates via stdio, so you won't see output unless connected to an MCP client.

## Extending the Server

### Adding New Research Sources
1. Create a new search method in `src/index.ts`
2. Add credibility scoring logic
3. Integrate into `handleDeepResearch`
4. Update the tool definitions

### Custom Decision Criteria
Modify the `handleWeightedDecision` method to add domain-specific weighting algorithms for your use cases.

## License

MIT License - feel free to use in your projects!

## Credits

Built with:
- [@modelcontextprotocol/sdk](https://github.com/modelcontextprotocol/typescript-sdk)
- [@google/generative-ai](https://www.npmjs.com/package/@google/generative-ai)
- [axios](https://axios-http.com/)
- [cheerio](https://cheerio.js.org/)

## Support

For issues or questions:
1. Check the Troubleshooting section above
2. Review Claude Code MCP documentation
3. Verify your API keys and configuration
4. Check server logs for detailed error messages
