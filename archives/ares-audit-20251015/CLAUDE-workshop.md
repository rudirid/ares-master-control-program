# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent System Overview

This workspace is equipped with a comprehensive suite of specialized AI agents designed to accelerate software development across the entire stack. Each agent is an expert in their domain and can be invoked to provide deep, focused assistance.

## Available Agents

### Architecture & Design

**@fullstack-architect**
- System architecture design and technical decisions
- Technology stack selection and trade-off analysis
- Integration planning (LLMs, APIs, databases)
- Scalability and performance architecture
- Use for: Starting new projects, architectural refactoring, design decisions

**Slash command:** `/arch`

---

### Frontend Development

**@frontend-architect**
- React, Next.js, Vue, Svelte development
- Component architecture and state management
- Modern UI patterns and performance optimization
- Styling (Tailwind, CSS-in-JS, Sass)
- Use for: Building SPAs, SSR apps, complex UIs

**Slash command:** `/frontend`

**Key capabilities:**
- React Server Components and streaming
- State management (Zustand, Redux, TanStack Query)
- Performance optimization (code splitting, memoization)
- Accessibility and responsive design
- TypeScript integration

---

### Backend Development

**@backend-architect**
- API design (REST, GraphQL, tRPC)
- Server-side logic and business rules
- Authentication and authorization
- API security and validation
- Use for: Building scalable APIs and backend services

**Slash command:** `/backend`

**Key capabilities:**
- Node.js, Python, Go, Rust backends
- Database integration and query optimization
- Microservices architecture
- Rate limiting and caching strategies
- Error handling and logging

---

### Database & Data

**@database-expert**
- Database schema design and normalization
- Query optimization and indexing
- Migrations and versioning
- Working with PostgreSQL, MongoDB, Redis, vector databases
- Use for: Schema design, query optimization, database migrations

**Slash command:** `/db`

**Key capabilities:**
- Prisma and Drizzle ORM expertise
- N+1 query prevention
- Connection pooling and transactions
- Redis caching patterns
- Vector database integration (pgvector, Pinecone)

---

### LLM Integration

**@llm-integration-expert**
- Integrating OpenAI, Anthropic Claude, and open-source LLMs
- Prompt engineering and optimization
- Streaming responses and function calling
- Cost optimization and token management
- Use for: Adding AI capabilities to applications

**Slash command:** `/llm`

**Key capabilities:**
- OpenAI and Anthropic Claude API integration
- Streaming implementations for real-time UX
- Function/tool calling patterns
- Error handling and retry logic
- Embeddings generation

**@rag-builder**
- Building RAG (Retrieval Augmented Generation) systems
- Document processing and chunking strategies
- Vector databases and semantic search
- Knowledge base Q&A systems
- Use for: Building AI assistants with custom knowledge

**Slash command:** `/rag`

**Key capabilities:**
- Document parsing (PDF, DOCX, Markdown, web)
- Chunking strategies (fixed-size, semantic, hierarchical)
- Vector database integration (Pinecone, Weaviate, Qdrant, pgvector)
- Hybrid search (semantic + keyword)
- RAG evaluation and optimization

---

### MCP Development

**@mcp-server-builder**
- Building Model Context Protocol servers
- Creating tools, resources, and prompts
- Extending LLM capabilities with custom functionality
- Use for: Building MCP integrations for Claude and other LLMs

**Slash command:** `/mcp`

**Key capabilities:**
- MCP server architecture (TypeScript/Python)
- Tool design and implementation
- Resource and prompt management
- Security and error handling
- Testing MCP servers

---

### DevOps & Deployment

**@devops-expert**
- Docker containerization and multi-stage builds
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Deployment strategies and infrastructure
- Kubernetes and container orchestration
- Use for: Setting up deployment pipelines, containerization, production ops

**Slash command:** `/deploy`

**Key capabilities:**
- Optimized Dockerfiles
- GitHub Actions and GitLab CI/CD
- Deployment to Vercel, Railway, AWS, GCP
- Infrastructure as Code (Terraform)
- Monitoring and observability

---

### Code Quality & Testing

**@code-reviewer**
- Code quality and best practices review
- Security vulnerability identification
- Performance optimization suggestions
- Maintainability assessment
- Use for: Getting thorough code reviews before merging

**Slash command:** `/review`

**Review coverage:**
- Security (SQL injection, XSS, auth issues)
- Performance (N+1 queries, algorithm complexity)
- Code quality (SOLID principles, naming, structure)
- Testing coverage and edge cases
- Language-specific best practices

**@test-engineer**
- Test strategy and implementation
- Unit, integration, and E2E tests
- Testing frameworks (Vitest, Jest, Pytest, Playwright)
- Test coverage and quality
- Use for: Writing comprehensive test suites

**Slash command:** `/test`

**Key capabilities:**
- Test-Driven Development (TDD)
- React Testing Library and component tests
- API testing (Supertest, FastAPI TestClient)
- E2E testing (Playwright, Cypress)
- Test factories and fixtures

---

### Web Scraping

**@web-scraper-expert**
- Web scraping and data extraction
- Crawling strategies and best practices
- Ethical scraping and legal considerations
- Use for: Extracting data from websites

**Key capabilities:**
- BeautifulSoup, Scrapy, Playwright, Puppeteer
- Handling dynamic content and JavaScript
- Anti-scraping countermeasures
- Data cleaning and validation
- Respecting robots.txt and rate limits

---

## Quick Reference: When to Use Which Agent

**Starting a new project?**
→ `/arch` - Get architectural guidance and technology recommendations

**Building the frontend?**
→ `/frontend` - React, Next.js, component architecture, state management

**Creating APIs?**
→ `/backend` - REST/GraphQL API design, authentication, business logic

**Designing database schemas?**
→ `/db` - Schema design, migrations, query optimization

**Adding AI features?**
→ `/llm` - LLM integration, prompt engineering, streaming
→ `/rag` - Building knowledge bases and document Q&A

**Extending Claude with custom tools?**
→ `/mcp` - Build MCP servers for custom functionality

**Ready to deploy?**
→ `/deploy` - Docker, CI/CD, deployment strategies

**Need code review?**
→ `/review` - Security, performance, quality assessment

**Writing tests?**
→ `/test` - Unit, integration, E2E tests

**Scraping data?**
→ `@web-scraper-expert` - Ethical web scraping and data extraction

---

## Agent Usage Patterns

### Sequential Agent Workflow

For complex projects, use agents in sequence:

1. **Architecture Phase**: `/arch` - Design system architecture
2. **Database Phase**: `/db` - Design schema and models
3. **Backend Phase**: `/backend` - Implement APIs
4. **Frontend Phase**: `/frontend` - Build UI
5. **Testing Phase**: `/test` - Write comprehensive tests
6. **Review Phase**: `/review` - Code quality check
7. **Deployment Phase**: `/deploy` - Set up CI/CD and deploy

### Parallel Agent Consultation

For specific features, consult multiple agents:

**Example: Building an AI-powered document search**
- `/arch` - Overall feature architecture
- `/rag` - RAG system implementation
- `/db` - Vector database setup
- `/backend` - API endpoints
- `/frontend` - Search UI
- `/test` - Testing strategy

### Specialist Deep Dives

When stuck on a specific problem, go deep with the specialist:

**Database Performance Issue:**
```
/db

I'm experiencing slow queries on my posts table. Here's my schema:
[paste schema]

And here's the slow query:
[paste query]

Can you help optimize this?
```

**LLM Integration Challenge:**
```
/llm

I need to implement streaming responses from Claude with function calling.
The user should see real-time updates while the LLM can call tools to fetch data.
How should I architect this?
```

---

## Best Practices for Working with Agents

**1. Be Specific**
- Provide context about your project
- Share relevant code snippets
- Explain what you've already tried

**2. Ask Follow-up Questions**
- Agents are experts - drill down on details
- Ask "why" to understand trade-offs
- Request examples and code samples

**3. Combine Agent Expertise**
- Use multiple agents for complex problems
- Get architecture advice, then implementation help
- Have code reviewed by multiple specialists

**4. Iterate and Refine**
- Start with high-level design
- Implement incrementally
- Review and optimize

---

## Development Workflow with Agents

### Feature Development Lifecycle

**1. Planning** (`/arch`)
```
What's the best architecture for a real-time collaborative editor with:
- Multiple users editing simultaneously
- Presence indicators
- Conflict resolution
- Offline support
```

**2. Database Design** (`/db`)
```
Design a schema for:
- Documents with version history
- User presence tracking
- Operational transform logs
- Optimize for real-time queries
```

**3. Backend Implementation** (`/backend`)
```
Build a WebSocket server for:
- Real-time collaboration
- Operational transforms
- User presence
- Authentication
```

**4. Frontend Implementation** (`/frontend`)
```
Create a collaborative editor UI with:
- Real-time synchronization
- User cursors and selections
- Optimistic updates
- Offline queue
```

**5. Testing** (`/test`)
```
Create tests for:
- Conflict resolution
- Presence synchronization
- Offline/online transitions
- Multi-user scenarios
```

**6. Review** (`/review`)
```
Review this collaborative editing implementation for:
- Race conditions
- Memory leaks
- Security issues
- Performance bottlenecks
```

**7. Deployment** (`/deploy`)
```
Set up deployment for:
- WebSocket server (needs sticky sessions)
- Horizontal scaling
- Database connection pooling
- Real-time monitoring
```

---

## Common Development Scenarios

### Scenario 1: Building a SaaS Application

```
/arch
I'm building a multi-tenant SaaS app for project management with:
- Team collaboration
- File uploads
- Real-time updates
- Role-based access control
- Usage-based billing
What's the best architecture?

→ [Get architecture recommendations]

/db
Design the database schema for this multi-tenant system.
Ensure proper data isolation between tenants.

→ [Get schema design]

/backend
Implement the authentication and tenant isolation middleware.

→ [Get implementation]

/frontend
Build the dashboard UI with real-time project updates.

→ [Get UI implementation]

/test
Create integration tests for tenant isolation.

→ [Get test suite]
```

### Scenario 2: Adding AI Features

```
/llm
I want to add an AI assistant that helps users write better project descriptions.
It should:
- Analyze current description
- Suggest improvements
- Stream responses in real-time

→ [Get LLM integration plan]

/rag
Users should be able to ask questions about all their project documentation.
How do I build this with RAG?

→ [Get RAG implementation]

/mcp
Create an MCP server that gives Claude access to:
- User's projects and tasks
- Team member information
- Project analytics

→ [Get MCP server code]
```

### Scenario 3: Performance Optimization

```
/db
My dashboard query is taking 5+ seconds with 1000 users.
Here's the query: [paste query]
Here's the schema: [paste schema]

→ [Get optimization strategy]

/review
Review this code for performance issues:
[paste code]

→ [Get performance review]

/deploy
Set up Redis caching for frequently accessed data.

→ [Get caching implementation]
```

---

## Technology Stack Recommendations

Based on the agents' expertise, here are recommended stacks:

### Full-Stack TypeScript (Recommended for most projects)

**Frontend:**
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- Shadcn/ui components
- Zustand (state) or TanStack Query (server state)

**Backend:**
- Next.js API Routes or tRPC
- Prisma or Drizzle ORM
- PostgreSQL
- Redis (caching)

**Deployment:**
- Vercel (frontend + serverless)
- Railway or Supabase (database)

**Why:** End-to-end type safety, fast development, great DX

### AI-Powered Applications

**Add to above:**
- OpenAI or Anthropic Claude API
- LangChain or LlamaIndex (for RAG)
- Pinecone or pgvector (vector database)
- Upstash Redis (caching)

**MCP Integration:**
- @modelcontextprotocol/sdk
- Custom MCP servers for Claude

### High-Performance Backend

**Stack:**
- Go or Rust (API server)
- PostgreSQL with read replicas
- Redis (caching + pub/sub)
- Docker + Kubernetes

**Why:** Maximum performance, handles high concurrency

---

## Development Guidelines

### Code Quality Standards

**TypeScript:**
- Strict mode enabled
- No `any` types (use `unknown` when needed)
- Comprehensive type definitions
- ESLint + Prettier

**Testing:**
- 80%+ code coverage on critical paths
- Unit tests for business logic
- Integration tests for APIs
- E2E tests for critical user flows

**Security:**
- Input validation on all endpoints
- Parameterized SQL queries (prevent injection)
- Authentication and authorization on protected routes
- Secrets in environment variables (never in code)
- HTTPS enforced in production

**Performance:**
- Database queries optimized (no N+1)
- Appropriate indexing
- Redis caching for expensive operations
- Code splitting and lazy loading (frontend)
- CDN for static assets

### Git Workflow

1. Create feature branch
2. Implement with agent assistance
3. Write tests (`/test`)
4. Get code review (`/review`)
5. Fix issues and iterate
6. Merge to main
7. Deploy (`/deploy`)

---

## Getting Help

### For Agent-Specific Questions

Each agent has deep expertise - don't hesitate to ask detailed questions:

```
/db
Why should I use a composite index instead of two separate indexes?
Can you show me the EXPLAIN ANALYZE output difference?
```

### For Multi-Agent Workflows

Describe your full use case:

```
I'm building a feature that requires:
- Real-time collaboration (backend)
- Optimistic UI updates (frontend)
- Event sourcing (database)
- WebSocket connections (devops)

Can you help me design this end-to-end?
```

### For Best Practices

Ask agents for recommendations:

```
/arch
What's the best way to handle file uploads in a multi-tenant SaaS?
Consider: security, storage, processing, and cost.
```

---

## Example Projects

### Starter Templates

The agents can help you create production-ready starters:

**SaaS Starter:**
```
/arch
Create a SaaS starter template with:
- Authentication (email + OAuth)
- Multi-tenancy
- Subscription billing
- Admin dashboard
- Role-based access control
```

**AI App Starter:**
```
/arch + /llm
Create an AI application starter with:
- Chat interface
- Streaming responses
- Conversation history
- RAG document Q&A
- Usage tracking
```

**API Service:**
```
/backend + /db
Create a REST API service with:
- CRUD operations
- Pagination
- Filtering and search
- Rate limiting
- API documentation (OpenAPI)
```

---

## Continuous Improvement

The agent system is designed to evolve with your needs:

**Custom Agents:**
- You can create specialized agents for your domain
- Add them to `~/.claude/agents/`
- Follow the existing agent format

**Slash Commands:**
- Create custom commands in `~/.claude/commands/`
- Combine multiple agents
- Automate common workflows

**Feedback Loop:**
- Use `/review` to learn from code reviews
- Ask agents to explain their recommendations
- Build your expertise while using the agents

---

## Summary

This workspace gives you access to a team of AI specialists covering:
- ✅ Full-stack architecture and design
- ✅ Frontend development (React, Next.js, etc.)
- ✅ Backend development (APIs, business logic)
- ✅ Database design and optimization
- ✅ LLM integration and prompt engineering
- ✅ RAG systems and vector databases
- ✅ MCP server development
- ✅ DevOps, Docker, and deployment
- ✅ Code review and quality assurance
- ✅ Testing strategies and implementation
- ✅ Web scraping and data extraction

**Use the slash commands for quick access, and don't hesitate to consult multiple agents for complex problems.**

Happy building! 🚀
