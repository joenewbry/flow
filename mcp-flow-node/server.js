#!/usr/bin/env node

/**
 * Flow MCP Server - Node.js implementation
 * Provides tools for interacting with Flow CLI via Model Context Protocol
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { ChromaClient } from "chromadb";
import fs from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class FlowMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: "flow",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.chromaClient = null;
    this.chromaInitialized = false;
    
    this.setupToolHandlers();
  }

  async ensureChromaInitialized() {
    if (!this.chromaInitialized) {
      try {
        // Import embedding functions
        const { DefaultEmbeddingFunction } = await import("chromadb");
        
        this.chromaClient = new ChromaClient({
          host: "localhost",
          port: 8000
        });
        
        // Use the same default embedding function as the Python client
        this.embeddingFunction = new DefaultEmbeddingFunction();
        
        await this.chromaClient.heartbeat();
        this.chromaInitialized = true;
        console.error("ChromaDB initialized for MCP server with default embedding function");
      } catch (error) {
        console.error(`Failed to initialize ChromaDB: ${error.message}`);
        throw error;
      }
    }
  }

  setupToolHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "what-can-i-do",
            description: "Get information about what you can do with Flow",
            inputSchema: {
              type: "object",
              properties: {},
              additionalProperties: false,
            },
          },
          {
            name: "search-screenshots",
            description: "Search OCR data from screenshots with optional date range parameters",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "Search query for the OCR text content",
                },
                start_date: {
                  type: "string",
                  description: "Start date for search (YYYY-MM-DD format, optional)",
                },
                end_date: {
                  type: "string",
                  description: "End date for search (YYYY-MM-DD format, optional)",
                },
                limit: {
                  type: "integer",
                  description: "Maximum number of results to return (default: 10)",
                  default: 10,
                },
              },
              required: ["query"],
              additionalProperties: false,
            },
          },
        ],
      };
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        let result;

        if (name === "what-can-i-do") {
          result = {
            flow_capabilities: [
              "Search for anything that you worked on while using flow. This includes urls, document titles, jira tickets, etc.",
              "Search OCR data from screenshots with optional date ranges"
            ],
            description: "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns.",
            available_tools: [
              "what-can-i-do",
              "search-screenshots"
            ]
          };
        } else if (name === "search-screenshots") {
          await this.ensureChromaInitialized();
          
          const query = args.query;
          const startDate = args.start_date;
          const endDate = args.end_date;
          const limit = args.limit || 10;
          
          // Build search parameters
          const searchParams = {
            queryTexts: [query],
            nResults: limit,
            include: ['documents', 'metadatas', 'distances']
          };
          
          // Add date filtering if provided
          if (startDate || endDate) {
            const whereClause = {};
            if (startDate) {
              whereClause.timestamp = { $gte: `${startDate}T00:00:00` };
            }
            if (endDate) {
              if (whereClause.timestamp) {
                whereClause.timestamp.$lte = `${endDate}T23:59:59`;
              } else {
                whereClause.timestamp = { $lte: `${endDate}T23:59:59` };
              }
            }
            searchParams.where = whereClause;
          }
          
          // Perform search
          const collection = await this.chromaClient.getCollection({ 
            name: "screenshots",
            embeddingFunction: this.embeddingFunction
          });
          const searchResults = await collection.query(searchParams);
          
          result = {
            query: query,
            results: searchResults.documents?.map((doc, index) => ({
              content: doc,
              metadata: searchResults.metadatas?.[index] || {},
              distance: searchResults.distances?.[index] || 0
            })) || [],
            total_found: searchResults.documents?.length || 0,
            date_range: {
              start_date: startDate,
              end_date: endDate
            }
          };
        } else {
          throw new Error(`Unknown tool: ${name}`);
        }

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        console.error(`Error executing tool ${name}:`, error);
        return {
          content: [
            {
              type: "text",
              text: `Error: ${error.message}`,
            },
          ],
          isError: true,
        };
      }
    });
  }


  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Flow MCP Server running on stdio transport");
  }
}

// Start the server
const server = new FlowMCPServer();
server.run().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
