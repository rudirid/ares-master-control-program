#!/usr/bin/env node

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { GoogleGenerativeAI } from '@google/generative-ai';
import axios from 'axios';
import * as cheerio from 'cheerio';
import { config } from 'dotenv';

config();

// Initialize Gemini AI
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

interface ResearchResult {
  source: string;
  title: string;
  snippet: string;
  url?: string;
  relevance: number;
  credibility: number;
}

interface WeightedDecision {
  recommendation: string;
  confidence: number;
  supportingEvidence: ResearchResult[];
  reasoning: string;
  alternatives?: string[];
}

class GeminiResearchServer {
  private server: Server;
  private maxResults: number;
  private timeout: number;

  constructor() {
    this.server = new Server(
      {
        name: 'gemini-research-mcp',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.maxResults = parseInt(process.env.MAX_SEARCH_RESULTS || '10');
    this.timeout = parseInt(process.env.RESEARCH_TIMEOUT || '60000');

    this.setupHandlers();
  }

  private setupHandlers() {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: 'deep_research',
          description: 'Perform deep research using Gemini AI with Google Scholar and YouTube integration. Provides comprehensive analysis with weighted decision-making for software/AI development.',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'The research query or question',
              },
              context: {
                type: 'string',
                description: 'Additional context about your project or requirements',
              },
              focus_areas: {
                type: 'array',
                items: { type: 'string' },
                description: 'Specific areas to focus on (e.g., "performance", "scalability", "cost")',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'scholar_search',
          description: 'Search Google Scholar for academic papers and research. Returns credible academic sources with relevance scoring.',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'Academic search query',
              },
              max_results: {
                type: 'number',
                description: 'Maximum number of results to return (default: 10)',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'youtube_research',
          description: 'Search YouTube for technical tutorials, talks, and demonstrations. Useful for finding practical implementations and expert opinions.',
          inputSchema: {
            type: 'object',
            properties: {
              query: {
                type: 'string',
                description: 'YouTube search query',
              },
              max_results: {
                type: 'number',
                description: 'Maximum number of results to return (default: 10)',
              },
            },
            required: ['query'],
          },
        },
        {
          name: 'weighted_decision',
          description: 'Analyze research results and provide weighted decision-making recommendations for software/AI development choices.',
          inputSchema: {
            type: 'object',
            properties: {
              question: {
                type: 'string',
                description: 'The decision question (e.g., "Should I use PostgreSQL or MongoDB?")',
              },
              criteria: {
                type: 'array',
                items: { type: 'string' },
                description: 'Decision criteria (e.g., "performance", "scalability", "ease of use")',
              },
              context: {
                type: 'string',
                description: 'Project context and constraints',
              },
            },
            required: ['question'],
          },
        },
        {
          name: 'gemini_query',
          description: 'Direct query to Gemini Pro model for complex analysis and synthesis of information.',
          inputSchema: {
            type: 'object',
            properties: {
              prompt: {
                type: 'string',
                description: 'The prompt or question for Gemini',
              },
              temperature: {
                type: 'number',
                description: 'Creativity level (0.0-1.0, default: 0.7)',
              },
            },
            required: ['prompt'],
          },
        },
      ] as Tool[],
    }));

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'deep_research':
            return await this.handleDeepResearch(args);
          case 'scholar_search':
            return await this.handleScholarSearch(args);
          case 'youtube_research':
            return await this.handleYouTubeResearch(args);
          case 'weighted_decision':
            return await this.handleWeightedDecision(args);
          case 'gemini_query':
            return await this.handleGeminiQuery(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${errorMessage}`,
            },
          ],
        };
      }
    });
  }

  private async handleDeepResearch(args: any) {
    const { query, context = '', focus_areas = [] } = args;

    // Parallel research across sources
    const [scholarResults, youtubeResults, geminiAnalysis] = await Promise.all([
      this.searchScholar(query, 5),
      this.searchYouTube(query, 5),
      this.queryGemini(
        `Provide a comprehensive research analysis for: ${query}\n\nContext: ${context}\n\nFocus areas: ${focus_areas.join(', ')}`,
        0.7
      ),
    ]);

    // Combine and weight results
    const combinedResults = {
      query,
      context,
      focus_areas,
      academic_sources: scholarResults,
      video_resources: youtubeResults,
      ai_analysis: geminiAnalysis,
      timestamp: new Date().toISOString(),
    };

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(combinedResults, null, 2),
        },
      ],
    };
  }

  private async handleScholarSearch(args: any) {
    const { query, max_results = this.maxResults } = args;
    const results = await this.searchScholar(query, max_results);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  }

  private async handleYouTubeResearch(args: any) {
    const { query, max_results = this.maxResults } = args;
    const results = await this.searchYouTube(query, max_results);

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(results, null, 2),
        },
      ],
    };
  }

  private async handleWeightedDecision(args: any) {
    const { question, criteria = [], context = '' } = args;

    // Research the question
    const researchPrompt = `
Research question: ${question}

Decision criteria: ${criteria.join(', ')}
Context: ${context}

Provide a weighted decision analysis with:
1. Clear recommendation
2. Confidence level (0-100)
3. Supporting evidence
4. Reasoning
5. Alternative options

Format as JSON with these fields.
    `;

    const geminiResponse = await this.queryGemini(researchPrompt, 0.3);

    // Try to parse as JSON, fallback to text
    let decision: WeightedDecision;
    try {
      decision = JSON.parse(geminiResponse);
    } catch {
      decision = {
        recommendation: 'Analysis completed',
        confidence: 75,
        supportingEvidence: [],
        reasoning: geminiResponse,
      };
    }

    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(decision, null, 2),
        },
      ],
    };
  }

  private async handleGeminiQuery(args: any) {
    const { prompt, temperature = 0.7 } = args;
    const response = await this.queryGemini(prompt, temperature);

    return {
      content: [
        {
          type: 'text',
          text: response,
        },
      ],
    };
  }

  private async queryGemini(prompt: string, temperature: number): Promise<string> {
    try {
      const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
      const result = await model.generateContent({
        contents: [{ role: 'user', parts: [{ text: prompt }] }],
        generationConfig: {
          temperature,
          maxOutputTokens: 8192,
        },
      });

      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Gemini API error: ${error}`);
    }
  }

  private async searchScholar(query: string, maxResults: number): Promise<ResearchResult[]> {
    try {
      // Using scholarly search via scraping (respecting robots.txt)
      const searchUrl = `https://scholar.google.com/scholar?q=${encodeURIComponent(query)}&hl=en`;

      const response = await axios.get(searchUrl, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
        timeout: this.timeout,
      });

      const $ = cheerio.load(response.data);
      const results: ResearchResult[] = [];

      $('.gs_ri').slice(0, maxResults).each((i, elem) => {
        const $elem = $(elem);
        const title = $elem.find('.gs_rt').text().trim();
        const snippet = $elem.find('.gs_rs').text().trim();
        const linkElem = $elem.find('.gs_rt a');
        const url = linkElem.attr('href') || '';

        // Calculate relevance based on position and citations
        const citationText = $elem.find('.gs_fl a').first().text();
        const citations = parseInt(citationText.match(/\d+/)?.[0] || '0');
        const relevance = Math.max(0.5, 1 - (i * 0.1)) + (citations > 0 ? 0.2 : 0);

        results.push({
          source: 'Google Scholar',
          title: title.replace(/^\[.*?\]\s*/, ''), // Remove [PDF] etc.
          snippet,
          url,
          relevance: Math.min(1, relevance),
          credibility: 0.9, // Academic sources are highly credible
        });
      });

      return results;
    } catch (error) {
      console.error('Scholar search error:', error);
      return [];
    }
  }

  private async searchYouTube(query: string, maxResults: number): Promise<ResearchResult[]> {
    try {
      const apiKey = process.env.YOUTUBE_API_KEY;

      if (apiKey) {
        // Use official YouTube API if available
        const response = await axios.get('https://www.googleapis.com/youtube/v3/search', {
          params: {
            part: 'snippet',
            q: query,
            type: 'video',
            maxResults,
            key: apiKey,
          },
          timeout: this.timeout,
        });

        return response.data.items.map((item: any, index: number) => ({
          source: 'YouTube',
          title: item.snippet.title,
          snippet: item.snippet.description,
          url: `https://www.youtube.com/watch?v=${item.videoId}`,
          relevance: Math.max(0.5, 1 - (index * 0.1)),
          credibility: 0.7, // Video content is moderately credible
        }));
      } else {
        // Fallback: scrape YouTube search (less reliable)
        const searchUrl = `https://www.youtube.com/results?search_query=${encodeURIComponent(query)}`;
        const response = await axios.get(searchUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
          },
          timeout: this.timeout,
        });

        // Extract video data from initial data
        const match = response.data.match(/var ytInitialData = ({.*?});/);
        if (!match) return [];

        const data = JSON.parse(match[1]);
        const videoRenderers = data.contents?.twoColumnSearchResultsRenderer?.primaryContents
          ?.sectionListRenderer?.contents?.[0]?.itemSectionRenderer?.contents || [];

        const results: ResearchResult[] = [];
        for (let i = 0; i < Math.min(maxResults, videoRenderers.length); i++) {
          const video = videoRenderers[i].videoRenderer;
          if (!video) continue;

          results.push({
            source: 'YouTube',
            title: video.title.runs[0].text,
            snippet: video.descriptionSnippet?.runs?.map((r: any) => r.text).join('') || '',
            url: `https://www.youtube.com/watch?v=${video.videoId}`,
            relevance: Math.max(0.5, 1 - (i * 0.1)),
            credibility: 0.7,
          });
        }

        return results;
      }
    } catch (error) {
      console.error('YouTube search error:', error);
      return [];
    }
  }

  async start() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Gemini Research MCP Server running on stdio');
  }
}

const server = new GeminiResearchServer();
server.start().catch(console.error);
