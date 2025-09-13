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

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "hello-world",
            description: "A simple hello world tool for testing MCP client connection",
            inputSchema: {
              type: "object",
              properties: {
                name: {
                  type: "string",
                  description: "Name to greet (optional)",
                  default: "World",
                },
              },
              additionalProperties: false,
            },
          },
        ],
      };
    });

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      if (name === "hello-world") {
        const nameToGreet = args?.name || "World";
        const result = {
          message: `Hello, ${nameToGreet}!`,
          status: "success",
          tool: "hello-world",
          timestamp: new Date().toISOString(),
        };

        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      }

      throw new Error(`Unknown tool: ${name}`);
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
