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
import { spawn } from "child_process";
import os from "os";

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
    
    // Process management
    this.chromaProcess = null;
    this.flowRunnerProcess = null;
    this.isRecording = false;
    
    // State persistence
    this.stateFile = path.join(__dirname, '.flow-state.json');
    this.workspaceRoot = path.resolve(__dirname, '..');
    this.refineryPath = path.join(this.workspaceRoot, 'refinery');
    
    this.setupToolHandlers();
    this.loadState();
  }

  async loadState() {
    try {
      const stateData = await fs.readFile(this.stateFile, 'utf8');
      const state = JSON.parse(stateData);
      this.isRecording = state.isRecording || false;
      console.error(`Loaded state: recording=${this.isRecording}`);
    } catch (error) {
      console.error(`No previous state found or error loading state: ${error.message}`);
      this.isRecording = false;
    }
  }

  async saveState() {
    try {
      const state = { isRecording: this.isRecording };
      await fs.writeFile(this.stateFile, JSON.stringify(state, null, 2));
      console.error(`Saved state: recording=${this.isRecording}`);
    } catch (error) {
      console.error(`Error saving state: ${error.message}`);
    }
  }

  async startChromaDB() {
    if (this.chromaProcess) {
      console.error("ChromaDB process already running");
      return;
    }

    try {
      console.error("Starting ChromaDB server...");
      
      // Change to refinery directory and start chroma using the virtual environment
      const chromaPath = path.join(this.refineryPath, '.venv', 'bin', 'chroma');
      
      // Check if chroma executable exists
      try {
        await fs.access(chromaPath);
      } catch (error) {
        throw new Error(`ChromaDB executable not found at ${chromaPath}. Make sure the virtual environment is set up correctly.`);
      }
      
      this.chromaProcess = spawn(chromaPath, ['run', '--host', 'localhost', '--port', '8000'], {
        cwd: this.refineryPath,
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      this.chromaProcess.stdout.on('data', (data) => {
        console.error(`ChromaDB stdout: ${data}`);
      });

      this.chromaProcess.stderr.on('data', (data) => {
        console.error(`ChromaDB stderr: ${data}`);
      });

      this.chromaProcess.on('close', (code) => {
        console.error(`ChromaDB process exited with code ${code}`);
        this.chromaProcess = null;
        this.chromaInitialized = false;
      });

      this.chromaProcess.on('error', (error) => {
        console.error(`ChromaDB process error: ${error.message}`);
        this.chromaProcess = null;
        this.chromaInitialized = false;
      });

      // Wait a moment for ChromaDB to start
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      console.error("ChromaDB server started");
    } catch (error) {
      console.error(`Failed to start ChromaDB: ${error.message}`);
      throw error;
    }
  }

  async stopChromaDB() {
    if (this.chromaProcess) {
      console.error("Stopping ChromaDB server...");
      this.chromaProcess.kill();
      this.chromaProcess = null;
      this.chromaInitialized = false;
      console.error("ChromaDB server stopped");
    }
  }

  async startFlowRunner() {
    if (this.flowRunnerProcess) {
      console.error("Flow runner process already running");
      return;
    }

    try {
      console.error("Starting Flow runner...");
      
      // Start the Python flow runner using the virtual environment
      const pythonPath = path.join(this.refineryPath, '.venv', 'bin', 'python');
      
      // Check if python executable exists
      try {
        await fs.access(pythonPath);
      } catch (error) {
        throw new Error(`Python executable not found at ${pythonPath}. Make sure the virtual environment is set up correctly.`);
      }
      
      // Check if run.py exists
      const runPyPath = path.join(this.refineryPath, 'run.py');
      try {
        await fs.access(runPyPath);
      } catch (error) {
        throw new Error(`run.py not found at ${runPyPath}. Make sure you're in the correct directory.`);
      }
      
      this.flowRunnerProcess = spawn(pythonPath, ['run.py'], {
        cwd: this.refineryPath,
        detached: false,
        stdio: ['ignore', 'pipe', 'pipe']
      });

      this.flowRunnerProcess.stdout.on('data', (data) => {
        console.error(`Flow runner stdout: ${data}`);
      });

      this.flowRunnerProcess.stderr.on('data', (data) => {
        console.error(`Flow runner stderr: ${data}`);
      });

      this.flowRunnerProcess.on('close', (code) => {
        console.error(`Flow runner process exited with code ${code}`);
        this.flowRunnerProcess = null;
        this.isRecording = false;
        this.saveState();
      });

      this.flowRunnerProcess.on('error', (error) => {
        console.error(`Flow runner process error: ${error.message}`);
        this.flowRunnerProcess = null;
        this.isRecording = false;
        this.saveState();
      });

      this.isRecording = true;
      await this.saveState();
      console.error("Flow runner started");
    } catch (error) {
      console.error(`Failed to start Flow runner: ${error.message}`);
      throw error;
    }
  }

  async stopFlowRunner() {
    if (this.flowRunnerProcess) {
      console.error("Stopping Flow runner...");
      this.flowRunnerProcess.kill();
      this.flowRunnerProcess = null;
      this.isRecording = false;
      await this.saveState();
      console.error("Flow runner stopped");
    }
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
          {
            name: "start-flow",
            description: "Start Flow screenshot recording (starts ChromaDB server and Python capture process)",
            inputSchema: {
              type: "object",
              properties: {},
              additionalProperties: false,
            },
          },
          {
            name: "stop-flow",
            description: "Stop Flow screenshot recording (stops Python capture process and ChromaDB server)",
            inputSchema: {
              type: "object",
              properties: {},
              additionalProperties: false,
            },
          },
          {
            name: "get-stats",
            description: "Get statistics about OCR data files and ChromaDB collection",
            inputSchema: {
              type: "object",
              properties: {},
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
              "Search OCR data from screenshots with optional date ranges",
              "Start and stop screenshot recording with ChromaDB integration",
              "Get statistics about captured data"
            ],
            description: "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns.",
            available_tools: [
              "what-can-i-do",
              "search-screenshots",
              "start-flow",
              "stop-flow",
              "get-stats"
            ],
            current_status: {
              recording: this.isRecording,
              chroma_running: this.chromaProcess !== null,
              flow_runner_running: this.flowRunnerProcess !== null
            }
          };
        } else if (name === "start-flow") {
          if (this.isRecording) {
            result = {
              success: true,
              message: "Flow recording is already running",
              status: {
                recording: this.isRecording,
                chroma_running: this.chromaProcess !== null,
                flow_runner_running: this.flowRunnerProcess !== null
              }
            };
          } else {
            await this.startChromaDB();
            await this.startFlowRunner();
            result = {
              success: true,
              message: "Flow recording started successfully",
              status: {
                recording: this.isRecording,
                chroma_running: this.chromaProcess !== null,
                flow_runner_running: this.flowRunnerProcess !== null
              }
            };
          }
        } else if (name === "stop-flow") {
          if (!this.isRecording) {
            result = {
              success: true,
              message: "Flow recording is already stopped",
              status: {
                recording: this.isRecording,
                chroma_running: this.chromaProcess !== null,
                flow_runner_running: this.flowRunnerProcess !== null
              }
            };
          } else {
            await this.stopFlowRunner();
            await this.stopChromaDB();
            result = {
              success: true,
              message: "Flow recording stopped successfully",
              status: {
                recording: this.isRecording,
                chroma_running: this.chromaProcess !== null,
                flow_runner_running: this.flowRunnerProcess !== null
              }
            };
          }
        } else if (name === "get-stats") {
          // Count OCR JSON files
          const ocrDir = path.join(this.refineryPath, 'data', 'ocr');
          let ocrFileCount = 0;
          try {
            const files = await fs.readdir(ocrDir);
            ocrFileCount = files.filter(file => file.endsWith('.json')).length;
          } catch (error) {
            console.error(`Error reading OCR directory: ${error.message}`);
          }

          // Get ChromaDB collection stats
          let chromaCount = 0;
          let chromaError = null;
          try {
            await this.ensureChromaInitialized();
            const collection = await this.chromaClient.getCollection({ 
              name: "screen_ocr_history",
              embeddingFunction: this.embeddingFunction
            });
            chromaCount = await collection.count();
          } catch (error) {
            chromaError = error.message;
            console.error(`Error getting ChromaDB stats: ${error.message}`);
          }

          result = {
            ocr_files: {
              count: ocrFileCount,
              directory: ocrDir
            },
            chroma_collection: {
              name: "screen_ocr_history",
              count: chromaCount,
              error: chromaError
            },
            recording_status: {
              active: this.isRecording,
              chroma_running: this.chromaProcess !== null,
              flow_runner_running: this.flowRunnerProcess !== null
            }
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
            name: "screen_ocr_history",
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


  async autoRestore() {
    if (this.isRecording) {
      try {
        console.error("Auto-restoring previous recording state...");
        await this.startChromaDB();
        await this.startFlowRunner();
        console.error("Successfully restored recording state");
      } catch (error) {
        console.error(`Failed to auto-restore recording state: ${error.message}`);
        this.isRecording = false;
        await this.saveState();
      }
    }
  }

  async cleanup() {
    console.error("Cleaning up processes...");
    if (this.flowRunnerProcess) {
      await this.stopFlowRunner();
    }
    if (this.chromaProcess) {
      await this.stopChromaDB();
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Flow MCP Server running on stdio transport");
    
    // Auto-restore state if it was recording before
    await this.autoRestore();
    
    // Handle cleanup on exit
    process.on('SIGTERM', () => this.cleanup());
    process.on('SIGINT', () => this.cleanup());
    process.on('exit', () => this.cleanup());
  }
}

// Start the server
const server = new FlowMCPServer();
server.run().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
