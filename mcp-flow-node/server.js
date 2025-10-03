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

// Enhanced logging utility
class Logger {
  constructor(name = 'FlowMCP') {
    this.name = name;
  }

  _log(level, message, ...args) {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${this.name}] [${level}]`;
    console.error(`${prefix} ${message}`, ...args);
  }

  info(message, ...args) {
    this._log('INFO', message, ...args);
  }

  warn(message, ...args) {
    this._log('WARN', message, ...args);
  }

  error(message, ...args) {
    this._log('ERROR', message, ...args);
  }

  debug(message, ...args) {
    if (process.env.DEBUG || process.env.FLOW_DEBUG) {
      this._log('DEBUG', message, ...args);
    }
  }
}

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class FlowMCPServer {
  constructor() {
    this.logger = new Logger('FlowMCPServer');
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
      this.logger.info(`Loaded state: recording=${this.isRecording}`);
    } catch (error) {
      this.logger.warn(`No previous state found or error loading state: ${error.message}`);
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
          {
            name: "activity-graph",
            description: "Generate activity timeline graph data showing when Flow was active capturing screens",
            inputSchema: {
              type: "object",
              properties: {
                days: {
                  type: "integer", 
                  description: "Number of days to include in the graph (default: 7)",
                  default: 7,
                },
                grouping: {
                  type: "string",
                  description: "How to group the data: 'hourly', 'daily' (default: 'hourly')",
                  enum: ["hourly", "daily"],
                  default: "hourly",
                },
                include_empty: {
                  type: "boolean",
                  description: "Include time periods with no activity (default: true)",
                  default: true,
                },
              },
              additionalProperties: false,
            },
          },
          {
            name: "time-range-summary",
            description: "Get a sampled summary of OCR data over a specified time range by returning up to 24 evenly distributed results",
            inputSchema: {
              type: "object",
              properties: {
                start_time: {
                  type: "string",
                  description: "Start time in ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD)",
                },
                end_time: {
                  type: "string",
                  description: "End time in ISO format (YYYY-MM-DDTHH:MM:SS) or date format (YYYY-MM-DD)",
                },
                max_results: {
                  type: "integer",
                  description: "Maximum number of results to return (default: 24, max: 100)",
                  default: 24,
                },
                include_text: {
                  type: "boolean",
                  description: "Include OCR text content in results (default: true)",
                  default: true,
                },
              },
              required: ["start_time", "end_time"],
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
              "Get statistics about captured data",
              "Generate activity timeline graphs showing when Flow was actively capturing screens",
              "Get time-range summaries with sampled OCR data (up to 24 evenly distributed results)"
            ],
            description: "Flow is a screen activity tracking and analysis tool that helps you search and analyze your work patterns.",
            available_tools: [
              "what-can-i-do",
              "search-screenshots",
              "start-flow",
              "stop-flow",
              "get-stats",
              "activity-graph",
              "time-range-summary"
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
        } else if (name === "activity-graph") {
          const days = args.days || 7;
          const grouping = args.grouping || "hourly";
          const includeEmpty = args.include_empty !== false;
          
          // Read and analyze OCR JSON files for activity data
          const ocrDir = path.join(this.refineryPath, 'data', 'ocr');
          let activityData = [];
          
          try {
            const files = await fs.readdir(ocrDir);
            const jsonFiles = files.filter(file => file.endsWith('.json'));
            
            // Calculate date range
            const endDate = new Date();
            const startDate = new Date(endDate.getTime() - (days * 24 * 60 * 60 * 1000));
            
            // Process files and extract timestamps
            for (const file of jsonFiles) {
              // Parse timestamp from filename: YYYY-MM-DDTHH-MM-SS-microseconds_ScreenName.json
              const match = file.match(/^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6})_(.+)\.json$/);
              if (match) {
                const timestampStr = match[1].replace(/-/g, ':').replace(/T(\d{2}):(\d{2}):(\d{2}):(\d{6})/, 'T$1:$2:$3.$4');
                const fileDate = new Date(timestampStr);
                
                if (fileDate >= startDate && fileDate <= endDate) {
                  try {
                    const filePath = path.join(ocrDir, file);
                    const fileContent = await fs.readFile(filePath, 'utf8');
                    const data = JSON.parse(fileContent);
                    
                    activityData.push({
                      timestamp: data.timestamp,
                      screen_name: data.screen_name,
                      text_length: data.text_length || 0,
                      word_count: data.word_count || 0,
                      has_content: (data.text_length || 0) > 0
                    });
                  } catch (error) {
                    console.error(`Error reading file ${file}:`, error.message);
                  }
                }
              }
            }
            
            // Group data by time period
            const groupedData = {};
            
            for (const activity of activityData) {
              const date = new Date(activity.timestamp);
              let key;
              
              if (grouping === "daily") {
                key = date.toISOString().split('T')[0]; // YYYY-MM-DD
              } else { // hourly
                const hour = date.getHours().toString().padStart(2, '0');
                key = `${date.toISOString().split('T')[0]} ${hour}:00`; // YYYY-MM-DD HH:00
              }
              
              if (!groupedData[key]) {
                groupedData[key] = {
                  timestamp: key,
                  capture_count: 0,
                  total_text_length: 0,
                  total_word_count: 0,
                  screens: new Set(),
                  has_content_count: 0
                };
              }
              
              groupedData[key].capture_count++;
              groupedData[key].total_text_length += activity.text_length;
              groupedData[key].total_word_count += activity.word_count;
              groupedData[key].screens.add(activity.screen_name);
              if (activity.has_content) {
                groupedData[key].has_content_count++;
              }
            }
            
            // Convert sets to arrays and calculate averages
            const timelineData = Object.values(groupedData).map(item => ({
              timestamp: item.timestamp,
              capture_count: item.capture_count,
              avg_text_length: Math.round(item.total_text_length / item.capture_count) || 0,
              avg_word_count: Math.round(item.total_word_count / item.capture_count) || 0,
              unique_screens: item.screens.size,
              content_percentage: Math.round((item.has_content_count / item.capture_count) * 100) || 0,
              screen_names: Array.from(item.screens)
            }));
            
            // Fill in empty periods if requested
            if (includeEmpty) {
              const allPeriods = [];
              const currentDate = new Date(startDate);
              
              while (currentDate <= endDate) {
                let key;
                if (grouping === "daily") {
                  key = currentDate.toISOString().split('T')[0];
                  currentDate.setDate(currentDate.getDate() + 1);
                } else { // hourly
                  const hour = currentDate.getHours().toString().padStart(2, '0');
                  key = `${currentDate.toISOString().split('T')[0]} ${hour}:00`;
                  currentDate.setHours(currentDate.getHours() + 1);
                }
                
                if (!groupedData[key]) {
                  allPeriods.push({
                    timestamp: key,
                    capture_count: 0,
                    avg_text_length: 0,
                    avg_word_count: 0,
                    unique_screens: 0,
                    content_percentage: 0,
                    screen_names: []
                  });
                } else {
                  allPeriods.push(timelineData.find(item => item.timestamp === key));
                }
              }
              
              timelineData.length = 0;
              timelineData.push(...allPeriods);
            }
            
            // Sort by timestamp
            timelineData.sort((a, b) => a.timestamp.localeCompare(b.timestamp));
            
            result = {
              graph_type: "activity_timeline",
              time_range: {
                start_date: startDate.toISOString(),
                end_date: endDate.toISOString(),
                days: days
              },
              grouping: grouping,
              data_summary: {
                total_captures: activityData.length,
                total_periods: timelineData.length,
                active_periods: timelineData.filter(d => d.capture_count > 0).length,
                unique_screens: [...new Set(activityData.map(a => a.screen_name))],
                date_range_actual: {
                  earliest: activityData.length > 0 ? Math.min(...activityData.map(a => new Date(a.timestamp))) : null,
                  latest: activityData.length > 0 ? Math.max(...activityData.map(a => new Date(a.timestamp))) : null
                }
              },
              timeline_data: timelineData,
              visualization_suggestions: {
                chart_types: ["line", "bar", "heatmap"],
                recommended_chart: "line",
                x_axis: "timestamp",
                y_axis_options: ["capture_count", "avg_text_length", "content_percentage"],
                recommended_y_axis: "capture_count",
                color_coding: "unique_screens or content_percentage",
                tips: [
                  "Use line chart to show activity trends over time",
                  "Bar chart works well for daily grouping",
                  "Heatmap is excellent for hourly data across multiple days",
                  "Color by content_percentage to highlight productive periods",
                  "Filter out zero values for cleaner visualization of active periods"
                ]
              }
            };
            
          } catch (error) {
            result = {
              error: `Failed to analyze activity data: ${error.message}`,
              graph_type: "activity_timeline",
              timeline_data: [],
              time_range: { days: days, grouping: grouping }
            };
          }
        } else if (name === "time-range-summary") {
          const startTime = args.start_time;
          const endTime = args.end_time;
          const maxResults = Math.min(args.max_results || 24, 100);
          const includeText = args.include_text !== false;
          
          try {
            // Parse time ranges - handle both date and datetime formats
            let startDate, endDate;
            
            if (startTime.includes('T')) {
              startDate = new Date(startTime);
            } else {
              startDate = new Date(`${startTime}T00:00:00`);
            }
            
            if (endTime.includes('T')) {
              endDate = new Date(endTime);
            } else {
              endDate = new Date(`${endTime}T23:59:59`);
            }
            
            if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
              throw new Error("Invalid date format. Use YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS format");
            }
            
            if (startDate >= endDate) {
              throw new Error("Start time must be before end time");
            }
            
            // Read and filter OCR files within time range
            const ocrDir = path.join(this.refineryPath, 'data', 'ocr');
            const files = await fs.readdir(ocrDir);
            const jsonFiles = files.filter(file => file.endsWith('.json'));
            
            let filteredData = [];
            
            for (const file of jsonFiles) {
              // Parse timestamp from filename: YYYY-MM-DDTHH-MM-SS-microseconds_ScreenName.json
              const match = file.match(/^(\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6})_(.+)\.json$/);
              if (match) {
                const timestampStr = match[1].replace(/-/g, ':').replace(/T(\d{2}):(\d{2}):(\d{2}):(\d{6})/, 'T$1:$2:$3.$4');
                const fileDate = new Date(timestampStr);
                
                if (fileDate >= startDate && fileDate <= endDate) {
                  try {
                    const filePath = path.join(ocrDir, file);
                    const fileContent = await fs.readFile(filePath, 'utf8');
                    const data = JSON.parse(fileContent);
                    
                    filteredData.push({
                      filename: file,
                      timestamp: data.timestamp,
                      screen_name: data.screen_name,
                      text_length: data.text_length || 0,
                      word_count: data.word_count || 0,
                      text: includeText ? data.text : undefined,
                      screenshot_path: data.screenshot_path,
                      source: data.source
                    });
                  } catch (error) {
                    console.error(`Error reading file ${file}:`, error.message);
                  }
                }
              }
            }
            
            // Sort by timestamp
            filteredData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
            
            // Sample the data if we have more items than maxResults
            let sampledData = filteredData;
            let samplingInfo = { sampled: false, total_items: filteredData.length };
            
            if (filteredData.length > maxResults) {
              samplingInfo.sampled = true;
              samplingInfo.step_size = Math.floor(filteredData.length / maxResults);
              samplingInfo.sampling_method = "evenly_distributed";
              
              sampledData = [];
              const step = filteredData.length / maxResults;
              
              for (let i = 0; i < maxResults; i++) {
                const index = Math.floor(i * step);
                if (index < filteredData.length) {
                  sampledData.push(filteredData[index]);
                }
              }
            }
            
            result = {
              summary_type: "time_range_sampling",
              time_range: {
                start_time: startDate.toISOString(),
                end_time: endDate.toISOString(),
                duration_hours: Math.round((endDate - startDate) / (1000 * 60 * 60) * 100) / 100
              },
              sampling_info: samplingInfo,
              results_summary: {
                total_items_in_range: filteredData.length,
                returned_items: sampledData.length,
                total_text_length: sampledData.reduce((sum, item) => sum + item.text_length, 0),
                total_word_count: sampledData.reduce((sum, item) => sum + item.word_count, 0),
                unique_screens: [...new Set(sampledData.map(item => item.screen_name))],
                time_span: {
                  earliest: sampledData.length > 0 ? sampledData[0].timestamp : null,
                  latest: sampledData.length > 0 ? sampledData[sampledData.length - 1].timestamp : null
                }
              },
              data: sampledData
            };
            
          } catch (error) {
            result = {
              error: `Failed to generate time range summary: ${error.message}`,
              summary_type: "time_range_sampling",
              time_range: {
                start_time: startTime,
                end_time: endTime
              },
              data: []
            };
          }
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
