#!/usr/bin/env node

/**
 * ARES MCP Server v2.5
 * Master Control Program exposing proven patterns as MCP tools
 *
 * Implements:
 * - Internal validation protocol
 * - Pattern matching from proven-patterns.md
 * - Tech success queries from tech-success-matrix.md
 * - "Show Your Work" transparent output
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from "@modelcontextprotocol/sdk/types.js";
import { readFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

// ES module dirname workaround
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Paths to Ares knowledge base
const ARES_BASE_DIR = join(__dirname, "../../ares-master-control-program");
const PROVEN_PATTERNS_PATH = join(ARES_BASE_DIR, "proven-patterns.md");
const TECH_MATRIX_PATH = join(ARES_BASE_DIR, "tech-success-matrix.md");
const CORE_DIRECTIVES_PATH = join(ARES_BASE_DIR, "ares-core-directives.md");

// Pattern data structure (simplified from Python library)
interface Pattern {
  id: string;
  tier: 1 | 2 | 3;
  name: string;
  description: string;
  successRate: number;
  usageCount: number;
  category: string;
  appliesTo: string[];
  evidence: string[];
  tradeOffs: string;
}

// Hardcoded patterns (from patterns.py)
const PATTERNS: Pattern[] = [
  {
    id: "modular_architecture_v1",
    tier: 1,
    name: "Modular Scraper Architecture",
    description: "Unified coordinator with specialized scrapers",
    successRate: 0.95,
    usageCount: 12,
    category: "architecture",
    appliesTo: ["scraping", "data_collection", "multi_source", "modular"],
    evidence: [
      "ASX Trading AI: 5+ scrapers",
      "Business Brain: 3+ agents",
      "Main coordinator: 687 lines",
    ],
    tradeOffs: "More files vs easier maintenance (acceptable)",
  },
  {
    id: "database_centric_v1",
    tier: 1,
    name: "Database-Centric Architecture",
    description: "SQLite as single source of truth",
    successRate: 1.0,
    usageCount: 15,
    category: "data",
    appliesTo: ["database", "persistence", "sqlite", "single_source_truth"],
    evidence: [
      "100% success rate across projects",
      "10MB database = 100K+ records",
      "Zero configuration",
    ],
    tradeOffs: "Perfect for <1M rows, migrate to PostgreSQL at scale",
  },
  {
    id: "hybrid_ai_rules_v1",
    tier: 1,
    name: "Rule-Based + AI Hybrid",
    description: "Rules catch 80%, AI enhances edge cases",
    successRate: 0.9,
    usageCount: 8,
    category: "ai",
    appliesTo: ["ai", "machine_learning", "fallback", "hybrid", "rules"],
    evidence: [
      "Business Brain: Works without API key",
      "ASX Trading: Sentiment analysis with fallback",
      "90% success rate",
    ],
    tradeOffs: "Works offline, explainable, but AI accuracy limited",
  },
  {
    id: "comprehensive_cli_v1",
    tier: 1,
    name: "Comprehensive CLI with Argparse",
    description: "Professional command-line interfaces",
    successRate: 0.95,
    usageCount: 10,
    category: "interface",
    appliesTo: ["cli", "command_line", "argparse", "interface"],
    evidence: [
      "Every Riord project has rich CLI",
      "Dry-run mode, log levels, multiple modes",
    ],
    tradeOffs: "More code upfront, but saves time in usage",
  },
  {
    id: "graceful_degradation_v1",
    tier: 1,
    name: "Graceful Degradation",
    description: "Works without APIs, fallback modes everywhere",
    successRate: 0.95,
    usageCount: 10,
    category: "reliability",
    appliesTo: ["error_handling", "fallback", "reliability", "graceful"],
    evidence: [
      "All systems work without API keys",
      "Hybrid AI + Rules pattern",
      "Try/except with fallback",
    ],
    tradeOffs: "More code, but system never fully fails",
  },
  {
    id: "local_sentiment_v2",
    tier: 2,
    name: "Local Sentiment Analysis",
    description: "300+ financial keywords, 37% accuracy",
    successRate: 0.37,
    usageCount: 3,
    category: "ai",
    appliesTo: ["sentiment", "nlp", "financial", "local"],
    evidence: [
      "37% win rate in trading",
      "300+ curated keywords",
      "Negation and intensifier handling",
    ],
    tradeOffs: "Zero API costs, but low accuracy (needs improvement)",
  },
];

// Create MCP server
const server = new Server(
  {
    name: "ares-mcp-server",
    version: "2.5.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Tool definitions
const TOOLS: Tool[] = [
  {
    name: "get_proven_patterns",
    description:
      "Retrieve Riord's proven coding patterns by tier (1=validated, 2=working, 3=experimental)",
    inputSchema: {
      type: "object",
      properties: {
        tier: {
          type: "number",
          description: "Filter by tier: 1 (validated), 2 (working), 3 (experimental)",
          enum: [1, 2, 3],
        },
        category: {
          type: "string",
          description: "Filter by category (architecture, data, ai, interface, reliability)",
        },
      },
    },
  },
  {
    name: "validate_approach",
    description:
      "Run Ares internal validation protocol on a proposed approach. Returns confidence score and recommended patterns.",
    inputSchema: {
      type: "object",
      properties: {
        task: {
          type: "string",
          description: "What needs to be done",
        },
        proposed_approach: {
          type: "string",
          description: "How you plan to do it",
        },
      },
      required: ["task", "proposed_approach"],
    },
  },
  {
    name: "recommend_pattern",
    description:
      "Get the best proven pattern recommendation for a specific task",
    inputSchema: {
      type: "object",
      properties: {
        task: {
          type: "string",
          description: "Description of what you want to build",
        },
      },
      required: ["task"],
    },
  },
  {
    name: "query_tech_success",
    description:
      "Get success rates and evidence for specific technologies from Riord's tech-success-matrix.md",
    inputSchema: {
      type: "object",
      properties: {
        technology: {
          type: "string",
          description: "Technology name (e.g., 'python', 'sqlite', 'fastapi')",
        },
      },
      required: ["technology"],
    },
  },
];

// List tools handler
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: TOOLS,
  };
});

// Call tool handler
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "get_proven_patterns": {
        const tier = args?.tier as number | undefined;
        const category = args?.category as string | undefined;

        let filtered = PATTERNS;

        if (tier) {
          filtered = filtered.filter((p) => p.tier === tier);
        }

        if (category) {
          filtered = filtered.filter((p) => p.category === category);
        }

        // Sort by tier (1 first) then success rate
        filtered.sort((a, b) => {
          if (a.tier !== b.tier) return a.tier - b.tier;
          return b.successRate - a.successRate;
        });

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(
                filtered.map((p) => ({
                  name: p.name,
                  tier: p.tier,
                  description: p.description,
                  successRate: `${(p.successRate * 100).toFixed(0)}%`,
                  usageCount: p.usageCount,
                  evidence: p.evidence,
                  tradeOffs: p.tradeOffs,
                })),
                null,
                2
              ),
            },
          ],
        };
      }

      case "validate_approach": {
        const task = args?.task as string;
        const approach = args?.proposed_approach as string;

        // Simple validation using pattern matching
        const lowerTask = (task + " " + approach).toLowerCase();
        const matchingPatterns = PATTERNS.filter((p) =>
          p.appliesTo.some((keyword) => lowerTask.includes(keyword))
        );

        // Calculate confidence
        let confidence = 0.5;
        if (matchingPatterns.some((p) => p.tier === 1)) {
          confidence = 0.9;
        } else if (matchingPatterns.some((p) => p.tier === 2)) {
          confidence = 0.65;
        }

        const level =
          confidence >= 0.8 ? "HIGH" : confidence >= 0.5 ? "MEDIUM" : "LOW";
        const decision =
          confidence >= 0.8
            ? "EXECUTE - Show work and proceed autonomously"
            : confidence >= 0.5
            ? "PROCEED WITH CAVEATS - Note uncertainties"
            : "ESCALATE - Present options and ask for input";

        return {
          content: [
            {
              type: "text",
              text: `## ARES Validation Result

**Task:** ${task}
**Approach:** ${approach}

### Internal Validation:
✓ Confidence: ${level} (${(confidence * 100).toFixed(0)}%)
✓ Patterns Matched: ${matchingPatterns.map((p) => p.name).join(", ") || "None"}
✓ Decision: ${decision}

### Recommended Patterns:
${matchingPatterns
  .map(
    (p) =>
      `- ${p.name} (Tier ${p.tier}): ${p.description}\n  Success Rate: ${(
        p.successRate * 100
      ).toFixed(0)}%`
  )
  .join("\n")}

${
  confidence < 0.8
    ? "\n⚠️  **Caveats:** Proceed with caution and measure results"
    : ""
}
`,
            },
          ],
        };
      }

      case "recommend_pattern": {
        const task = args?.task as string;
        const lowerTask = task.toLowerCase();

        // Find matching patterns
        const matches = PATTERNS.filter((p) =>
          p.appliesTo.some((keyword) => lowerTask.includes(keyword))
        ).sort((a, b) => {
          if (a.tier !== b.tier) return a.tier - b.tier;
          return b.successRate - a.successRate;
        });

        if (matches.length === 0) {
          return {
            content: [
              {
                type: "text",
                text: `No proven patterns found for: "${task}"\n\nThis might be a new problem space. Consider starting with simple approach and documenting as Tier 3 pattern if successful.`,
              },
            ],
          };
        }

        const recommended = matches[0];

        return {
          content: [
            {
              type: "text",
              text: `## Recommended Pattern for: "${task}"

**${recommended.name}** (Tier ${recommended.tier})

${recommended.description}

**Success Rate:** ${(recommended.successRate * 100).toFixed(0)}%
**Used:** ${recommended.usageCount} times

**Evidence:**
${recommended.evidence.map((e) => `- ${e}`).join("\n")}

**Trade-offs:**
${recommended.tradeOffs}

${
  matches.length > 1
    ? `\n**Alternatives:**\n${matches
        .slice(1, 3)
        .map((p) => `- ${p.name} (Tier ${p.tier})`)
        .join("\n")}`
    : ""
}
`,
            },
          ],
        };
      }

      case "query_tech_success": {
        const tech = (args?.technology as string).toLowerCase();

        // Hardcoded tech success data (from tech-success-matrix.md)
        const techData: Record<string, any> = {
          python: {
            successRate: 0.95,
            usage: "Primary language across 3 projects",
            wins: [
              "Pandas + NumPy perfect for data analysis",
              "Requests + BeautifulSoup for web scraping",
              "FastAPI for modern APIs",
              "SQLite3 for POC databases",
            ],
            whenToUse: [
              "Data analysis projects",
              "Web scraping",
              "API backends",
              "POC/MVP development",
            ],
          },
          sqlite: {
            successRate: 1.0,
            usage: "All Python projects",
            wins: [
              "File-based storage: No server setup",
              "Zero configuration",
              "10MB database = 100K+ records",
            ],
            whenToUse: [
              "POC/MVP development",
              "Single-user applications",
              "<1M rows",
            ],
            whenNotToUse: [
              "Multi-user concurrent writes (use PostgreSQL)",
              ">1M rows with complex queries (use PostgreSQL)",
            ],
          },
          fastapi: {
            successRate: 0.9,
            usage: "Modern API framework",
            wins: [
              "Async support for parallel operations",
              "Auto-generated OpenAPI docs",
              "Type-safe with Pydantic",
              "Business Brain API built in <1 day",
            ],
            whenToUse: ["API backends", "Async processing", "Type safety needed"],
          },
        };

        const data = techData[tech];

        if (!data) {
          return {
            content: [
              {
                type: "text",
                text: `No success data found for "${tech}".\n\nAvailable technologies: ${Object.keys(
                  techData
                ).join(", ")}`,
              },
            ],
          };
        }

        return {
          content: [
            {
              type: "text",
              text: `## Tech Success: ${tech.toUpperCase()}

**Success Rate:** ${(data.successRate * 100).toFixed(0)}%
**Usage:** ${data.usage}

**What Works:**
${data.wins.map((w: string) => `- ${w}`).join("\n")}

**When to Use:**
${data.whenToUse.map((u: string) => `- ${u}`).join("\n")}

${
  data.whenNotToUse
    ? `\n**When NOT to Use:**\n${data.whenNotToUse
        .map((u: string) => `- ${u}`)
        .join("\n")}`
    : ""
}
`,
            },
          ],
        };
      }

      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    const errorMessage =
      error instanceof Error ? error.message : String(error);
    return {
      content: [{ type: "text", text: `Error: ${errorMessage}` }],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("ARES MCP Server v2.5 running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
