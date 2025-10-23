# Advanced Usage Guide

## Combining Tools for Maximum Insight

### Multi-Stage Research Pipeline

**Scenario**: Choosing a database for a new project

```
Step 1: Use scholar_search to find "distributed database performance benchmarks"
Step 2: Use youtube_research to find "PostgreSQL vs MongoDB production experience"
Step 3: Use weighted_decision with all the gathered context
```

This gives you:
- Academic benchmarks (credibility: 0.9)
- Real-world practitioner insights (credibility: 0.7)
- AI synthesis with weighted recommendations

### Iterative Refinement

Start broad, then narrow:

```
1. deep_research: "microservices architecture patterns"
2. scholar_search: "service mesh performance comparison"
3. gemini_query: "Detailed comparison of Istio vs Linkerd for a fintech application with PCI compliance requirements"
4. weighted_decision: "Should we implement service mesh now or later?"
```

## Custom Workflows

### Technology Evaluation Framework

```python
# In Claude Code conversation:
"""
I'm evaluating [TECHNOLOGY]. Please use this framework:

1. Use deep_research with focus_areas: ["maturity", "performance", "security", "cost", "community"]

2. Use scholar_search for academic validation

3. Use youtube_research to find production war stories

4. Use weighted_decision with criteria:
   - Production readiness (weight: 30%)
   - Performance at scale (weight: 25%)
   - Security posture (weight: 20%)
   - Total cost of ownership (weight: 15%)
   - Developer experience (weight: 10%)

5. Use gemini_query for final synthesis: "Given all research, provide implementation roadmap with risks"
"""
```

### Architecture Decision Records (ADRs)

Generate comprehensive ADRs:

```
Use deep_research for "[DECISION]" with context "[PROJECT CONTEXT]"

Then use gemini_query to format results as an ADR:
- Status: Proposed
- Context: [from research]
- Decision: [weighted recommendation]
- Consequences: [from analysis]
- Alternatives Considered: [from research]
```

## Optimizing Research Quality

### Focus Areas Strategy

Generic focus areas (less useful):
```javascript
focus_areas: ["good", "fast", "cheap"]
```

Specific focus areas (much better):
```javascript
focus_areas: [
  "p99 latency under 100ms",
  "horizontal scaling to 1M users",
  "AWS deployment cost < $500/month",
  "team learning curve < 2 weeks"
]
```

### Context Engineering

Poor context:
```
context: "building an app"
```

Rich context:
```
context: `
Building a real-time stock trading platform:
- Expected load: 10K concurrent users, 1M trades/day
- Tech stack: Node.js, React, PostgreSQL
- Team: 3 full-stack developers
- Timeline: 6 months to MVP
- Compliance: SEC regulations, SOC2
- Budget: $100K infrastructure/year
`
```

### Criteria Weighting

For `weighted_decision`, order criteria by importance:

```javascript
criteria: [
  "must handle 10K concurrent WebSocket connections",  // Deal-breaker
  "automatic failover < 30s downtime",                 // Critical
  "developer productivity",                             // Important
  "community ecosystem size"                            // Nice-to-have
]
```

The AI will weight earlier criteria more heavily.

## Integration Patterns

### With Existing Research

Combine with your own findings:

```
I've already researched [TOPIC] and found [FINDINGS].

Use deep_research to validate my findings and discover what I might have missed.
Specifically focus on [GAPS IN MY RESEARCH].
```

### Decision Matrices

Create comprehensive comparison matrices:

```
Use deep_research for each option:
1. "Kubernetes for container orchestration"
2. "Docker Swarm for container orchestration"
3. "AWS ECS for container orchestration"

Then use weighted_decision to create a comparison matrix with:
- Setup complexity
- Operating cost
- Learning curve
- Vendor lock-in
- Community support
- Enterprise features
```

## Advanced Gemini Queries

### Structured Analysis

```
Use gemini_query with temperature 0.2:
"Analyze the following architecture options and return ONLY valid JSON:

{
  "options": [
    {
      "name": "Option A",
      "pros": ["..."],
      "cons": ["..."],
      "score": 0-100,
      "best_for": "...",
      "worst_for": "..."
    }
  ],
  "recommendation": "...",
  "confidence": 0-100
}

Options to analyze: [YOUR OPTIONS]
Evaluation criteria: [YOUR CRITERIA]
"
```

### Comparative Analysis

```
Use gemini_query at temperature 0.3:
"Create a detailed comparison table:

| Criterion | Option A | Option B | Winner | Reasoning |
|-----------|----------|----------|--------|-----------|

Criteria:
1. Performance (weight: 30%)
2. Developer Experience (weight: 25%)
3. Cost (weight: 20%)
4. Scalability (weight: 15%)
5. Security (weight: 10%)

Provide specific metrics and cite sources where possible."
```

## Performance Optimization

### Parallel Research

Run independent queries simultaneously:

```
Please run these in parallel:
1. scholar_search: "graph database performance"
2. youtube_research: "Neo4j production deployment"
3. gemini_query: "Use cases where graph databases outperform relational"

Then synthesize findings.
```

### Caching Strategy

For repetitive research, document findings:

```
Use deep_research and save results to a local file.
For future related decisions, reference the file instead of re-researching.
```

## Domain-Specific Applications

### Machine Learning Projects

```
Research framework:
1. scholar_search: Latest academic papers on [TECHNIQUE]
2. youtube_research: Implementation tutorials and gotchas
3. gemini_query: "Compare this approach vs alternatives for [USE CASE]"
4. weighted_decision: Model selection with criteria [ACCURACY, SPEED, COST]
```

### Security Analysis

```
Security research workflow:
1. scholar_search: "vulnerability analysis [TECHNOLOGY]"
2. gemini_query: "Known attack vectors and CVEs for [TECHNOLOGY]"
3. weighted_decision: "Risk assessment for using [TECHNOLOGY] in [CONTEXT]"
```

### Cloud Architecture

```
Cloud decision framework:
1. deep_research with focus: ["regional availability", "pricing tiers", "egress costs"]
2. youtube_research: "AWS vs GCP vs Azure for [WORKLOAD]"
3. weighted_decision with TCO analysis over 3 years
```

## Best Practices

### 1. Always Provide Context
The more context you provide, the better the recommendations. Include:
- Team size and expertise
- Timeline constraints
- Budget limitations
- Regulatory requirements
- Existing tech stack
- Scale requirements

### 2. Validate Critical Decisions
For high-stakes decisions:
```
1. Use deep_research
2. Manually verify top 3 sources
3. Use weighted_decision
4. Use gemini_query to identify blind spots
5. Document decision rationale
```

### 3. Iterate on Queries
If results aren't useful:
- Make queries more specific
- Add concrete metrics to focus_areas
- Provide more context
- Lower temperature for factual answers
- Raise temperature for creative solutions

### 4. Combine Quantitative and Qualitative
```
Use scholar_search for benchmarks and data
Use youtube_research for community sentiment
Use gemini_query to synthesize both perspectives
```

### 5. Document Your Research
Create a research log:
```markdown
## Research: [DECISION]
Date: [DATE]
Researcher: [NAME]

### Query
[Your question]

### Sources Consulted
- Scholar: [query]
- YouTube: [query]
- Gemini: [query]

### Key Findings
[Summary]

### Decision
[Final choice]

### Rationale
[Reasoning based on weighted evidence]
```

## Troubleshooting Advanced Usage

### Too Many Results
Set `max_results: 3` for focused research:
```
scholar_search with query "..." and max_results 3
```

### Results Too Generic
Add domain-specific terms:
```
Instead of: "best database"
Use: "time-series database for IoT sensor data at 100K writes/sec"
```

### Low Confidence Scores
Provide more decision criteria and context:
```javascript
criteria: [
  "specific metric 1",
  "specific metric 2",
  "specific metric 3"
]
context: "detailed project info with constraints"
```

### Contradictory Findings
Use Gemini to reconcile:
```
Use gemini_query: "I found contradictory information:
Source A says: [...]
Source B says: [...]

Please analyze which is more applicable to my use case: [CONTEXT]
Consider recency, methodology, and relevance."
```

## Example: Complete Research Session

```
Task: Choose authentication method for mobile app

1. Use deep_research:
   query: "mobile app authentication methods 2025"
   context: "React Native app, 100K users, handling financial data"
   focus_areas: ["security", "user experience", "implementation complexity", "cost"]

2. Use scholar_search:
   query: "OAuth 2.0 vs JWT security vulnerabilities mobile applications"

3. Use youtube_research:
   query: "implementing Auth0 vs Firebase authentication React Native production"

4. Use weighted_decision:
   question: "Should we use Auth0, Firebase Auth, or custom JWT implementation?"
   criteria: [
     "security compliance with financial regulations",
     "session management at scale",
     "development time",
     "ongoing cost at 100K users",
     "mobile-specific features (biometric, etc.)"
   ]
   context: "Previous research findings + our team has React expertise but limited security expertise"

5. Use gemini_query:
   "Based on the decision to use [CHOICE], create a detailed implementation plan:
   - Architecture diagram needs
   - Security checklist
   - Migration strategy from current state
   - Testing approach
   - Rollout plan
   Format as actionable tasks with time estimates."
```

## Going Further

### Build Custom Workflows
Save commonly-used research workflows as templates.

### Integration with Other MCP Servers
Combine with:
- File system MCP for saving research
- Database MCP for storing decisions
- Git MCP for committing ADRs

### Feedback Loop
After implementing decisions:
1. Document actual results
2. Compare to research predictions
3. Refine your research criteria
4. Improve context engineering

This creates a continuously improving research process.
