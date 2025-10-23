# Ares MCP Server - Implementation Guide

**Quick Start Guide for Converting Ares to MCP Server**

---

## Prerequisites

**Install MCP SDK:**
```bash
pip install mcp
```

**Verify Installation:**
```bash
python -c "import mcp; print(mcp.__version__)"
```

---

## Phase 1: MVP (4-6 hours)

### Step 1: Set Up Basic Server Structure (30 min)

**Create:** `.ares-mcp/mcp/server.py`

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
import asyncio

app = Server('ares-mcp-server', version='1.0.0')

@app.list_tools()
async def list_tools():
    return []  # Start empty

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    raise ValueError(f'Unknown tool: {name}')

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

if __name__ == '__main__':
    asyncio.run(main())
```

**Test:**
```bash
python .ares-mcp/mcp/server.py
# Should start and wait for input (Ctrl+C to stop)
```

### Step 2: Add First Tool - submit_task (1 hour)

**Add to server.py:**

```python
from mcp.types import Tool, TextContent
import json
from pathlib import Path
from datetime import datetime

TASK_QUEUE_FILE = Path.home() / ".ares-mcp" / "mobile_task_queue.json"

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name='submit_task',
            description='Submit a task to Ares',
            inputSchema={
                'type': 'object',
                'properties': {
                    'task': {'type': 'string', 'description': 'Task description'}
                },
                'required': ['task']
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == 'submit_task':
        # Load queue
        if TASK_QUEUE_FILE.exists():
            with open(TASK_QUEUE_FILE, 'r') as f:
                queue = json.load(f)
        else:
            queue = []

        # Create task
        task = {
            'id': len(queue) + 1,
            'task': arguments['task'],
            'timestamp': datetime.now().isoformat(),
            'status': 'pending',
            'created_via': 'mcp'
        }
        queue.append(task)

        # Save queue
        with open(TASK_QUEUE_FILE, 'w') as f:
            json.dump(queue, f, indent=2)

        result = {'success': True, 'task_id': task['id']}
        return [TextContent(type='text', text=json.dumps(result))]

    raise ValueError(f'Unknown tool: {name}')
```

**Test with MCP Inspector:**
```bash
# Install inspector
npm install -g @modelcontextprotocol/inspector

# Test server
npx @modelcontextprotocol/inspector python .ares-mcp/mcp/server.py
```

### Step 3: Configure Claude Desktop (15 min)

**File:** `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
**Or:** `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

```json
{
  "mcpServers": {
    "ares": {
      "command": "python",
      "args": ["C:\\Users\\riord\\.ares-mcp\\mcp\\server.py"]
    }
  }
}
```

**Restart Claude Desktop**

**Test in Claude:**
```
"Use the submit_task tool to add 'Test MCP integration' to the queue"
```

Should see tool call and success response!

### Step 4: Add get_task_queue Tool (30 min)

```python
@app.list_tools()
async def list_tools():
    return [
        # ... submit_task ...
        Tool(
            name='get_task_queue',
            description='Get all queued tasks',
            inputSchema={'type': 'object', 'properties': {}}
        )
    ]

# In call_tool:
elif name == 'get_task_queue':
    if TASK_QUEUE_FILE.exists():
        with open(TASK_QUEUE_FILE, 'r') as f:
            queue = json.load(f)
    else:
        queue = []

    result = {'success': True, 'count': len(queue), 'tasks': queue}
    return [TextContent(type='text', text=json.dumps(result, indent=2))]
```

### Step 5: Add First Resource (30 min)

```python
from mcp.types import Resource

@app.list_resources()
async def list_resources():
    return [
        Resource(
            uri='ares://patterns/proven',
            name='Ares Proven Patterns',
            description='Validated coding patterns',
            mimeType='text/markdown'
        )
    ]

@app.read_resource()
async def read_resource(uri: str):
    if uri == 'ares://patterns/proven':
        patterns_file = Path.home() / ".ares-mcp" / "proven-patterns.md"
        content = patterns_file.read_text(encoding='utf-8')

        return {
            'contents': [{
                'uri': uri,
                'mimeType': 'text/markdown',
                'text': content
            }]
        }

    raise ValueError(f'Unknown resource: {uri}')
```

**Test in Claude:**
```
"Read the ares://patterns/proven resource and summarize the Tier 1 patterns"
```

### Step 6: Add Ares Protocol Formatting (1 hour)

```python
def format_task_with_ares_protocols(task: dict) -> str:
    return f"""Ares Master Control: Execute Task

Task: {task['task']}

Execute with Ares v2.1 protocols:
- Internal validation (confidence-based execution)
- Show your work (transparent reasoning)
- Apply proven patterns from ares://patterns/proven

Task ID: {task['id']}
"""

# Update submit_task to return formatted prompt:
result = {
    'success': True,
    'task_id': task['id'],
    'formatted_prompt': format_task_with_ares_protocols(task)
}
```

**MVP Complete!** You now have:
- ✅ Task submission tool
- ✅ Task queue retrieval
- ✅ Knowledge resource access
- ✅ Ares protocol formatting

---

## Phase 2: Knowledge Integration (3-4 hours)

### Step 1: Add All Knowledge Resources (1 hour)

```python
@app.list_resources()
async def list_resources():
    return [
        Resource(uri='ares://patterns/proven', ...),
        Resource(uri='ares://decisions/causality', ...),
        Resource(uri='ares://tech/success-matrix', ...),
        Resource(uri='ares://directives/core', ...),
        Resource(uri='ares://evolution/timeline', ...),
    ]
```

### Step 2: Add Pattern Query Tool (1.5 hours)

```python
Tool(
    name='query_proven_patterns',
    description='Search proven patterns by keyword and tier',
    inputSchema={
        'type': 'object',
        'properties': {
            'query': {'type': 'string', 'description': 'Search term'},
            'tier': {'type': 'string', 'enum': ['1', '2', '3', 'all']}
        },
        'required': ['query']
    }
)
```

**Implementation:** Text search through proven-patterns.md

### Step 3: Add Validation Tool (1 hour)

```python
Tool(
    name='validate_approach',
    description='Run Ares internal validation on an approach',
    inputSchema={
        'type': 'object',
        'properties': {
            'approach_description': {'type': 'string'},
            'complexity': {'type': 'string', 'enum': ['simple', 'medium', 'complex']}
        },
        'required': ['approach_description']
    }
)
```

**Implementation:** Return validation checklist from Ares directives

### Step 4: Test Knowledge Integration (30 min)

**Test Commands:**
```
"Query proven patterns for 'modular architecture' at tier 1"
"Validate this approach: Using SQLite for data storage"
"Read the ares://directives/core resource and summarize the internal validation loop"
```

---

## Phase 3: WhatsApp Integration (2-3 hours)

### Step 1: WhatsApp Send Tool (1 hour)

```python
import requests

Tool(
    name='send_whatsapp_message',
    description='Send message via WhatsApp bridge',
    inputSchema={
        'type': 'object',
        'properties': {
            'message': {'type': 'string'},
            'to_number': {'type': 'string', 'description': 'Optional recipient'}
        },
        'required': ['message']
    }
)

# In call_tool:
elif name == 'send_whatsapp_message':
    response = requests.post(
        'http://localhost:5000/send',
        json={'message': arguments['message']}
    )
    return [TextContent(type='text', text=response.text)]
```

**Prerequisite:** WhatsApp bridge must be running

### Step 2: Add Task Categorization (30 min)

```python
def categorize_task_content(task: str) -> str:
    content_lower = task.lower()
    if any(kw in content_lower for kw in ['build', 'create', 'fix']):
        return 'code'
    elif any(kw in content_lower for kw in ['research', 'analyze']):
        return 'research'
    # ... etc
    return 'general'
```

### Step 3: Update submit_task with Auto-Categorization (30 min)

```python
# In submit_task:
category = categorize_task_content(arguments['task'])
task['category'] = category

# Format based on category
formatted_prompt = format_task_by_category(task, category)
```

### Step 4: Test End-to-End (30 min)

**Test Flow:**
1. Start WhatsApp bridge: `python .ares-mcp/whatsapp_bridge.py`
2. Start MCP server (via Claude Desktop)
3. In Claude: "Submit task: Build a REST API"
4. Verify task queued
5. In Claude: "Send WhatsApp message: Task received"
6. Check phone for message

---

## Phase 4: Advanced Features (4-6 hours)

### Priority Features

**1. Task Completion Tracking (1 hour)**
```python
Tool(name='complete_task', ...)
```

**2. Task Status Query (30 min)**
```python
Tool(name='get_task_status', inputSchema={'task_id': number})
```

**3. Daemon Stats (30 min)**
```python
Tool(name='get_daemon_stats', ...)
# Read from daemon process
```

**4. Multi-User Support (1.5 hours)**
```python
# Add user authentication
# Track tasks by user
# User-specific permissions
```

**5. Task Dependencies (1.5 hours)**
```python
# Add 'depends_on' field
# Check dependencies before execution
# Trigger dependent tasks on completion
```

**6. SQLite Migration (1 hour)**
```python
# Replace JSON with SQLite
# Schema: tasks, users, history
# Better querying and concurrency
```

---

## Testing Strategy

### Unit Tests

```python
# test_mcp_server.py
import pytest
from mcp_server import categorize_task_content, format_task_with_ares_protocols

def test_categorize_code_task():
    assert categorize_task_content("Build a REST API") == "code"

def test_categorize_research_task():
    assert categorize_task_content("Research GraphQL vs REST") == "research"

def test_format_code_task():
    task = {'id': 1, 'task': 'Test', 'category': 'code'}
    prompt = format_task_with_ares_protocols(task)
    assert "Ares Master Control" in prompt
    assert "Internal validation" in prompt
```

### Integration Tests

```python
# test_integration.py
async def test_submit_and_retrieve_task():
    # Call submit_task
    result = await call_tool('submit_task', {'task': 'Test task'})
    task_id = json.loads(result[0].text)['task_id']

    # Call get_task_status
    status = await call_tool('get_task_status', {'task_id': task_id})
    assert 'Test task' in status[0].text
```

### MCP Inspector Testing

```bash
# Test all tools
npx @modelcontextprotocol/inspector python .ares-mcp/mcp/server.py

# In inspector:
# 1. List tools → Should show all 13 tools
# 2. Call submit_task → Success
# 3. Call get_task_queue → Shows submitted task
# 4. Read ares://patterns/proven → Returns markdown
```

### Claude Desktop Testing

**Test Script:**
```
1. "List all available Ares tools"
2. "Submit a task: Test MCP integration"
3. "Get the task queue"
4. "Read the proven patterns resource"
5. "Query proven patterns for 'modular'"
6. "Validate this approach: Using FastAPI"
7. "Send WhatsApp message: MCP test successful"
8. "Mark task #1 as completed with result: Test passed"
```

---

## Deployment

### Development Setup

```json
{
  "mcpServers": {
    "ares-dev": {
      "command": "python",
      "args": ["C:\\Users\\riord\\.ares-mcp\\mcp\\server.py"],
      "env": {
        "ARES_ENV": "development",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Production Setup

```json
{
  "mcpServers": {
    "ares": {
      "command": "python",
      "args": ["C:\\Users\\riord\\.ares-mcp\\mcp\\server.py"],
      "env": {
        "ARES_ENV": "production",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Remote Access (HTTP SSE)

**For team/remote access:**

```python
# mcp/server_remote.py
from mcp.server.sse import sse_server

app = FastAPI()

@app.get("/sse")
async def handle_sse(request: Request):
    async with sse_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

# Run with: uvicorn mcp.server_remote:app
```

---

## Troubleshooting

### Issue: MCP server not showing in Claude Desktop

**Solutions:**
1. Check config file path is correct
2. Restart Claude Desktop completely
3. Check command path: `python` vs `python3`
4. Verify Python version ≥3.10
5. Check server starts: `python .ares-mcp/mcp/server.py`

### Issue: Tools not appearing

**Solutions:**
1. Check `list_tools()` returns Tool objects (not dicts)
2. Verify inputSchema is valid JSON Schema
3. Check for syntax errors in server.py
4. Test with MCP inspector first

### Issue: Resource reading fails

**Solutions:**
1. Check file paths are absolute
2. Verify files exist: `ls .ares-mcp/*.md`
3. Check file encoding (should be UTF-8)
4. Test with: `python -c "from pathlib import Path; print(Path.home() / '.ares-mcp')"`

### Issue: WhatsApp integration not working

**Solutions:**
1. Verify bridge is running: `curl http://localhost:5000/tasks`
2. Check ngrok tunnel is active (if using webhook)
3. Test send endpoint: `curl -X POST http://localhost:5000/send -d '{"message":"test"}'`
4. Check bridge logs for errors

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def load_proven_patterns():
    patterns_file = Path.home() / ".ares-mcp" / "proven-patterns.md"
    return patterns_file.read_text(encoding='utf-8')
```

### Async File Operations

```python
import aiofiles

async def read_resource_async(filepath: Path):
    async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
        return await f.read()
```

### Database for Large Queues

```python
import sqlite3

# When queue > 100 tasks, migrate to SQLite
conn = sqlite3.connect('.ares-mcp/ares.db')
conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    task TEXT,
    status TEXT,
    created_at TEXT
)''')
```

---

## Next Steps After Implementation

1. **Document Usage** - Create user guide with examples
2. **Share with Community** - Open-source on GitHub
3. **Blog Post** - Write about Ares MCP architecture
4. **Demo Video** - Record usage demo
5. **Iterate** - Add features based on actual usage

---

## Resources

**MCP Documentation:**
- Official Docs: https://modelcontextprotocol.io/
- SDK Reference: https://github.com/modelcontextprotocol/python-sdk
- Examples: https://github.com/modelcontextprotocol/servers

**Ares Documentation:**
- `.ares-mcp/ARES_MCP_ANALYSIS.md` - Full analysis
- `.ares-mcp/MCP_QUICK_SUMMARY.md` - Executive summary
- `.ares-mcp/mcp_server_sample.py` - Sample implementation

**Community:**
- MCP Discord: [Link from official site]
- GitHub Discussions: modelcontextprotocol/python-sdk

---

**Ready to start? Begin with Phase 1 MVP - 4-6 hours to working prototype!**

Generated: 2025-10-15
Guide Version: 1.0
