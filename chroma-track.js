import screenshot from 'screenshot-desktop';

import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Anthropic } from '@anthropic-ai/sdk';
import dotenv from 'dotenv';
import readline from 'readline';

// Helper function to convert filename-style timestamps to ISO 8601
function convertFilenameTimestampToISO(ts) {
  if (typeof ts !== 'string') return ts;

  if (ts.includes('T') && ts.includes(':') && (ts.includes('.') || ts.endsWith('Z')) && !isNaN(new Date(ts).getTime())) {
    return ts;
  }

  const parts = ts.split('T');
  if (parts.length !== 2) {
    return ts;
  }

  let timePart = parts[1];
  const zSuffix = timePart.endsWith('Z') ? 'Z' : '';
  if (zSuffix) {
    timePart = timePart.slice(0, -1);
  }

  const timeSegments = timePart.split('-');
  if (timeSegments.length === 4) {
    return `${parts[0]}T${timeSegments[0]}:${timeSegments[1]}:${timeSegments[2]}.${timeSegments[3]}${zSuffix}`;
  } else if (timeSegments.length === 3) {
    return `${parts[0]}T${timeSegments[0]}:${timeSegments[1]}:${timeSegments[2]}${zSuffix}`;
  }

  return ts;
}

// Get current file's directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Initialize environment variables
dotenv.config();

// Initialize Anthropic client
const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

// Initialize vector store (Chroma)
let vectorStore;
async function initializeVectorStore() {
  try {
    console.log('Initializing Chroma store...');
    const chromaOptions = {
      collectionName: 'screen_history',
      serverUrl: process.env.CHROMA_SERVER_URL || 'http://localhost:8000'
    };
    vectorStore = await createSimpleChromaStore(chromaOptions.collectionName, chromaOptions.serverUrl);
    console.log('Chroma store initialized successfully');
    return vectorStore;
  } catch (error) {
    console.error('Vector store initialization error:', error.message);
    return null;
  }
}

// Ensure directories exist
async function ensureDirectories() {
  const screenshotsDir = path.join(__dirname, 'screenshots');
  const screenhistoryDir = path.join(__dirname, 'screenhistory');
  
  for (const dir of [screenshotsDir, screenhistoryDir]) {
    try {
      await fs.mkdir(dir, { recursive: true });
    } catch (err) {
      if (err.code !== 'EEXIST') throw err;
    }
  }
  
  return { screenshotsDir, screenhistoryDir };
}

// Convert buffer to base64
function bufferToBase64(buffer) {
  return buffer.toString('base64');
}

// Process screenshot with Claude
async function processScreenshotWithClaude(imageBase64) {
  try {
    console.log('Sending request to Claude...');
    const response = await anthropic.messages.create({
      model: 'claude-3-7-sonnet-20250219',
      max_tokens: 1000,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'text',
              text: 'Analyze this screenshot and provide a detailed description in the following JSON format: { "active_app": "", "summary": "", "extracted_text": "", "task_category": "", "productivity_score": 0, "workflow_suggestions": "", "user_generated_text": "" }. For user_generated_text, include any text that appears to be typed by the user (like messages, emails, code comments, documents being written, etc.) but exclude UI elements, menus, and system text.'
            },
            {
              type: 'image',
              source: {
                type: 'base64',
                media_type: 'image/jpeg',
                data: imageBase64
              }
            }
          ]
        }
      ]
    });

    const cleanedResponse = response.content[0].text
      .replace(/```json\n?/g, '')
      .replace(/```\n?/g, '')
      .trim();
    
    return JSON.parse(cleanedResponse);
  } catch (error) {
    console.error('Claude API Error:', error.message);
    return null;
  }
}

// Process screenshot with OCR
async function processScreenshotWithOCR(imageBuffer) {
  try {
    console.log('Processing screenshot with OCR...');
    
    // Dynamic import for Tesseract
    const { createWorker } = await import('tesseract.js');
    
    const worker = await createWorker('eng');
    
    // Convert buffer to base64 for Tesseract
    const base64Image = bufferToBase64(imageBuffer);
    
    const { data: { text } } = await worker.recognize(`data:image/jpeg;base64,${base64Image}`);
    
    await worker.terminate();
    
    // Create a simplified analysis object with OCR results
    const analysis = {
      active_app: 'OCR Mode',
      summary: `OCR extracted ${text.length} characters of text`,
      extracted_text: text.trim(),
      task_category: 'text_extraction',
      productivity_score: 0,
      workflow_suggestions: '',
      user_generated_text: text.trim()
    };
    
    console.log(`OCR completed. Extracted ${text.length} characters.`);
    return analysis;
  } catch (error) {
    console.error('OCR Error:', error.message);
    return null;
  }
}

// Add JSON data to vector store
async function addToVectorStore(collection, analysisData) {
  try {
    const textToEmbed = `${analysisData.summary} ${analysisData.extracted_text}`;
    
    if (!analysisData.timestamp || isNaN(new Date(analysisData.timestamp).getTime())) {
      console.error(`Invalid or missing timestamp in analysisData for addToVectorStore. Timestamp: ${analysisData.timestamp}. Data:`, analysisData);
      return; 
    }

    await collection.add({
      id: analysisData.timestamp,
      document: textToEmbed,
      metadata: { ...analysisData },
    });
  } catch (error) {
    console.error(`Vector store add error for ID ${analysisData.timestamp}:`, error.message);
  }
}

// Load existing history into Chroma store
async function loadExistingHistory(collection, screenhistoryDir) {
  console.log('Starting to load existing screen history into Chroma store...');
  const startTime = Date.now();
  
  try {
    const files = await fs.readdir(screenhistoryDir);
    const jsonFiles = files.filter(file => path.extname(file).toLowerCase() === '.json');
    console.log(`Found ${jsonFiles.length} JSON files to process`);

    const batchSize = 100;
    let processedCount = 0;
    let currentBatch = [];
    
    for (const file of jsonFiles) {
      const filePath = path.join(screenhistoryDir, file);
      try {
        const fileContent = await fs.readFile(filePath, 'utf-8');
        let analysis = null;
        
        if (fileContent.trim() === 'null' || fileContent.trim() === '') {
          continue;
        }

        try {
          analysis = JSON.parse(fileContent);
        } catch (parseError) {
          console.warn(`Skipping ${file}: Could not parse JSON. Error: ${parseError.message}`);
          continue;
        }

        if (analysis && typeof analysis.summary === 'string' && typeof analysis.extracted_text === 'string') {
          let isoTimestamp = analysis.timestamp;
          
          if (isoTimestamp && typeof isoTimestamp === 'string') {
            if (isNaN(new Date(isoTimestamp).getTime()) || ((isoTimestamp.match(/-/g) || []).length > 2 && !isoTimestamp.includes(':'))) {
              isoTimestamp = convertFilenameTimestampToISO(analysis.timestamp);
            }
          }
          
          if (!isoTimestamp || isNaN(new Date(isoTimestamp).getTime())) {
            console.warn(`Skipping file ${file}: Invalid timestamp`);
            continue;
          }
          
          analysis.timestamp = isoTimestamp;
          
          // Check if this ID already exists in Chroma
          let exists = false;
          try {
            const existing = await collection.collection.get({ ids: [analysis.timestamp] });
            if (existing && existing.ids && existing.ids[0] && existing.ids[0].length > 0) {
              exists = true;
            }
          } catch (e) {
            exists = false;
          }
          
          if (exists) {
            continue;
          }
          
          // Prepare for batch insertion
          const textToEmbed = `${analysis.summary} ${analysis.extracted_text}`;
          currentBatch.push({
            id: analysis.timestamp,
            document: textToEmbed,
            metadata: analysis
          });

          // Process batch when it reaches batchSize
          if (currentBatch.length >= batchSize) {
            await collection.addBatch(currentBatch);
            processedCount += currentBatch.length;
            currentBatch = [];

            // Progress logging
            if (processedCount % 100 === 0) {
              const elapsed = Date.now() - startTime;
              const rate = processedCount / elapsed * 1000;
              const remaining = jsonFiles.length - processedCount;
              const estimatedTimeRemaining = remaining / rate / 60;
              const currentTimestamp = new Date().toISOString();

              console.log(`[${currentTimestamp}] Progress: ${processedCount}/${jsonFiles.length} files processed. Estimated time remaining: ${estimatedTimeRemaining.toFixed(1)} minutes`);
            }
          }
        }
        
      } catch (err) {
        console.error(`Error processing history file ${file}: ${err.message}`);
      }
    }

    // Process remaining items in the last batch
    if (currentBatch.length > 0) {
      await collection.addBatch(currentBatch);
      processedCount += currentBatch.length;
    }
    
    const totalTime = (Date.now() - startTime) / 1000;
    console.log(`Finished loading ${processedCount} files into Chroma store in ${totalTime.toFixed(1)} seconds`);
    
    // Display stats
    const stats = await collection.getStats();
    console.log(`Chroma collection stats:`, stats);
    
  } catch (err) {
    console.error(`Error reading screenhistory directory: ${err.message}`);
  }
}

// Global state for pause functionality
let isPaused = false;
let useOCR = false; // New flag for OCR mode
let rl;

// Initialize readline interface for keyboard input
function initializeReadline() {
  rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
  
  // Handle raw input to capture single characters
  process.stdin.setRawMode(true);
  process.stdin.resume();
  process.stdin.setEncoding('utf8');
  
  let inputBuffer = '';
  
  process.stdin.on('data', (key) => {
    // Handle Ctrl+C to exit
    if (key === '\u0003') {
      console.log('\nExiting...');
      process.exit();
    }
    
    // Handle backspace
    if (key === '\u007f' || key === '\u0008') {
      if (inputBuffer.length > 0) {
        inputBuffer = inputBuffer.slice(0, -1);
        process.stdout.write('\b \b');
      }
      return;
    }
    
    // Handle enter key
    if (key === '\r' || key === '\n') {
      if (inputBuffer === '/') {
        showMenu();
      }
      inputBuffer = '';
      return;
    }
    
    // Add character to buffer and echo it
    inputBuffer += key;
    process.stdout.write(key);
  });
}

// Show interactive menu
function showMenu() {
  const pauseResumeText = isPaused ? 'Resume tracking' : 'Pause tracking';
  const ocrModeText = useOCR ? 'Switch to Claude' : 'Switch to OCR';
  console.log('\n\n=== Screen Tracking Menu ===');
  console.log(`p - ${pauseResumeText}`);
  console.log(`o - ${ocrModeText}`);
  console.log('s - Show status');
  console.log('d - Generate daily summary');
  console.log('q - Quit');
  console.log('========================');
  console.log('Enter your choice: ');
  
  // Listen for single character input
  process.stdin.once('data', (key) => {
    const choice = key.toString().toLowerCase();
    
    switch (choice) {
      case 'p':
        togglePause();
        break;
      case 'o':
        toggleOCRMode();
        break;
      case 's':
        showStatus();
        break;
      case 'd':
        generateDailySummary();
        break;
      case 'q':
        console.log('\nExiting...');
        process.exit();
        break;
      default:
        console.log('\nInvalid choice. Press / to show menu again.');
    }
  });
}

// Toggle pause state
function togglePause() {
  isPaused = !isPaused;
  const status = isPaused ? 'PAUSED' : 'RESUMED';
  console.log(`\nScreen tracking ${status}`);
  if (!isPaused) {
    console.log('Resuming tracking...');
  }
}

// Toggle OCR mode
function toggleOCRMode() {
  useOCR = !useOCR;
  const mode = useOCR ? 'OCR' : 'Claude';
  console.log(`\nSwitched to ${mode} mode`);
  if (useOCR) {
    console.log('Note: OCR mode provides basic text extraction without detailed analysis');
  }
}

// Show current status
function showStatus() {
  console.log('\n=== Current Status ===');
  console.log(`Tracking: ${isPaused ? 'PAUSED' : 'ACTIVE'}`);
  console.log(`Mode: ${useOCR ? 'OCR' : 'Claude'}`);
  console.log(`Timestamp: ${new Date().toISOString()}`);
  console.log('=====================');
}

// Main tracking function
async function trackScreen() {
  try {
    console.log('Starting screen tracking...');
    console.log('Type "/" to access the menu');
    console.log(`Initial mode: ${useOCR ? 'OCR' : 'Claude'}`);
    
    // Initialize keyboard input handling
    initializeReadline();
    
    const { screenshotsDir, screenhistoryDir } = await ensureDirectories();
    const collection = await initializeVectorStore();

    if (!collection) {
      throw new Error('Failed to initialize vector store');
    }

    await loadExistingHistory(collection, screenhistoryDir);

    // Main loop for capturing new screenshots
    while (true) {
      // Check if paused
      if (isPaused) {
        await new Promise(resolve => setTimeout(resolve, 1000)); // Check every second
        continue;
      }
      
      const now = new Date();
      const currentISOTimestamp = now.toISOString();
      const filenameTimestamp = currentISOTimestamp.replace(/[:.]/g, '-');

      const screenshotPath = path.join(screenshotsDir, `${filenameTimestamp}.jpg`);
      const jsonPath = path.join(screenhistoryDir, `${filenameTimestamp}.json`);
      
      const img = await screenshot();
      await fs.writeFile(screenshotPath, img);
      
      let analysis;
      if (useOCR) {
        analysis = await processScreenshotWithOCR(img);
      } else {
        const base64Image = bufferToBase64(img);
        analysis = await processScreenshotWithClaude(base64Image);
      }
      
      if (analysis) {
        analysis.timestamp = currentISOTimestamp;
        await fs.writeFile(jsonPath, JSON.stringify(analysis, null, 2));
        await addToVectorStore(collection, analysis);
      }
      
      const waitTimeSeconds = 60;
      await new Promise(resolve => setTimeout(resolve, waitTimeSeconds * 1000));
    }
  } catch (error) {
    console.error('Error in screen tracking:', error);
    console.log('Restarting trackScreen in 5 seconds due to error...');
    await new Promise(resolve => setTimeout(resolve, 5000));
    trackScreen();
  }
}

// Start tracking
console.log(`Script boot time: ${new Date().toISOString()}`);
console.log('Initializing screen tracking script...');
trackScreen().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

// Simple ChromaDB approach using built-in embeddings
class SimpleChromaStore {
  constructor(chromaClient, collectionName = 'screen_history') {
    this.client = chromaClient;
    this.collectionName = collectionName;
    this.collection = null;
    console.log('SimpleChromaStore initialized.');
  }

  async initialize() {
    try {
      this.collection = await this.client.getOrCreateCollection({
        name: this.collectionName,
        metadata: { 
          description: "Screen tracking history with timestamps and metadata",
          version: "1.0"
        }
      });
      console.log(`SimpleChroma collection '${this.collectionName}' ready.`);
      return this.collection;
    } catch (error) {
      console.error('SimpleChromaStore initialization error:', error.message);
      throw error;
    }
  }

  async add(item) {
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized. Call initialize() first.');
      }

      const metadata = {
        date: new Date(item.metadata.timestamp).toISOString().split('T')[0],
        active_app: item.metadata.active_app || 'unknown',
        timestamp: item.metadata.timestamp,
        summary: item.metadata.summary || '',
        extracted_text: item.metadata.extracted_text || '',
        task_category: item.metadata.task_category || '',
        productivity_score: item.metadata.productivity_score || 0,
        user_generated_text: item.metadata.user_generated_text || ''
      };

      await this.collection.upsert({
        ids: [item.id],
        documents: [item.document],
        metadatas: [metadata]
      });

      console.log(`SimpleChromaStore: Added item ${item.id}`);
    } catch (error) {
      console.error(`SimpleChromaStore add error for id ${item.id}:`, error.message);
    }
  }

  async addBatch(items) {
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized. Call initialize() first.');
      }

      const ids = items.map(item => item.id);
      const documents = items.map(item => item.document);
      const metadatas = items.map(item => ({
        date: new Date(item.metadata.timestamp).toISOString().split('T')[0],
        active_app: item.metadata.active_app || 'unknown',
        timestamp: item.metadata.timestamp,
        summary: item.metadata.summary || '',
        extracted_text: item.metadata.extracted_text || '',
        task_category: item.metadata.task_category || '',
        productivity_score: item.metadata.productivity_score || 0,
        user_generated_text: item.metadata.user_generated_text || ''
      }));

      await this.collection.upsert({
        ids: ids,
        documents: documents,
        metadatas: metadatas
      });

      console.log(`SimpleChromaStore: Added batch of ${items.length} items`);
    } catch (error) {
      console.error('SimpleChromaStore batch add error:', error.message);
    }
  }

  async query(queryOptions) {
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized. Call initialize() first.');
      }

      const results = await this.collection.query({
        queryTexts: [queryOptions.queryText],
        nResults: queryOptions.nResults || 5
      });

      let formattedResults = this.formatResults(results);
      
      if (queryOptions.where && typeof queryOptions.where === 'function') {
        formattedResults = formattedResults.filter(result => queryOptions.where(result.metadata));
      }
      
      return formattedResults;
    } catch (error) {
      console.error('SimpleChromaStore query error:', error.message);
      return [];
    }
  }

  formatResults(chromaResults) {
    if (!chromaResults.documents || !chromaResults.documents[0]) {
      return [];
    }

    const documents = chromaResults.documents[0];
    const metadatas = chromaResults.metadatas[0] || [];
    const distances = chromaResults.distances[0] || [];

    return documents.map((document, index) => ({
      document: document,
      metadata: metadatas[index] || {},
      distance: distances[index] || 0
    }));
  }

  async getStats() {
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized.');
      }

      const count = await this.collection.count();
      return {
        totalDocuments: count,
        collectionName: this.collectionName
      };
    } catch (error) {
      console.error('SimpleChromaStore stats error:', error.message);
      return { totalDocuments: 0, collectionName: this.collectionName };
    }
  }
}

// Factory function for simple Chroma store
async function createSimpleChromaStore(collectionName = 'screen_history', chromaServerUrl = 'http://localhost:8000') {
  try {
    const { ChromaClient } = await import('chromadb');
    
    const client = new ChromaClient({
      path: chromaServerUrl
    });

    const vectorStore = new SimpleChromaStore(client, collectionName);
    await vectorStore.initialize();
    
    return vectorStore;
  } catch (error) {
    console.error('Failed to create SimpleChromaStore:', error.message);
    throw error;
  }
}

// Generate daily summary
async function generateDailySummary() {
  try {
    console.log('\n=== Daily Summary Generation ===');
    
    // Get date input from user
    const date = await getUserDateInput();
    if (!date) {
      console.log('Summary generation cancelled.');
      return;
    }
    
    console.log(`\nGenerating summary for ${date}...`);
    
    // Get all data for the specified date
    const dailyData = await getDailyData(date);
    
    if (dailyData.length === 0) {
      console.log(`No data found for ${date}`);
      return;
    }
    
    console.log(`Found ${dailyData.length} screenshots for ${date}`);
    
    // Generate summary
    const summary = await generateSummaryWithClaude(dailyData, date);
    
    if (summary) {
      // Save summary to file
      await saveSummaryToFile(summary, date);
      console.log(`Daily summary saved to ${date}-summary.md`);
    } else {
      console.log('Failed to generate summary');
    }
    
  } catch (error) {
    console.error('Error generating daily summary:', error.message);
  }
}

// Get date input from user
async function getUserDateInput() {
  return new Promise((resolve) => {
    console.log('\nEnter date for summary (YYYY-MM-DD format):');
    console.log('Examples: 2024-01-15, 2024-12-01');
    console.log('Press Enter for today, or type "cancel" to cancel:');
    
    let inputBuffer = '';
    
    const handleInput = (key) => {
      // Handle Ctrl+C
      if (key === '\u0003') {
        resolve(null);
        return;
      }
      
      // Handle backspace
      if (key === '\u007f' || key === '\u0008') {
        if (inputBuffer.length > 0) {
          inputBuffer = inputBuffer.slice(0, -1);
          process.stdout.write('\b \b');
        }
        return;
      }
      
      // Handle enter
      if (key === '\r' || key === '\n') {
        process.stdin.off('data', handleInput);
        
        if (inputBuffer.trim() === '' || inputBuffer.trim().toLowerCase() === 'today') {
          // Use today's date
          const today = new Date().toISOString().split('T')[0];
          resolve(today);
        } else if (inputBuffer.trim().toLowerCase() === 'cancel') {
          resolve(null);
        } else {
          // Validate date format
          const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
          if (dateRegex.test(inputBuffer.trim())) {
            const date = new Date(inputBuffer.trim());
            if (!isNaN(date.getTime())) {
              resolve(inputBuffer.trim());
            } else {
              console.log('\nInvalid date. Please use YYYY-MM-DD format.');
              resolve(null);
            }
          } else {
            console.log('\nInvalid format. Please use YYYY-MM-DD format.');
            resolve(null);
          }
        }
        return;
      }
      
      // Add character to buffer
      inputBuffer += key;
      process.stdout.write(key);
    };
    
    process.stdin.on('data', handleInput);
  });
}

// Get all data for a specific date
async function getDailyData(date) {
  try {
    const { screenhistoryDir } = await ensureDirectories();
    const files = await fs.readdir(screenhistoryDir);
    const jsonFiles = files.filter(file => path.extname(file).toLowerCase() === '.json');
    
    const dailyData = [];
    
    for (const file of jsonFiles) {
      const filePath = path.join(screenhistoryDir, file);
      try {
        const fileContent = await fs.readFile(filePath, 'utf-8');
        
        if (fileContent.trim() === 'null' || fileContent.trim() === '') {
          continue;
        }
        
        const analysis = JSON.parse(fileContent);
        if (analysis && analysis.timestamp) {
          const fileDate = new Date(analysis.timestamp).toISOString().split('T')[0];
          if (fileDate === date) {
            dailyData.push(analysis);
          }
        }
      } catch (error) {
        console.warn(`Error reading file ${file}:`, error.message);
      }
    }
    
    // Sort by timestamp
    dailyData.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    
    return dailyData;
  } catch (error) {
    console.error('Error getting daily data:', error.message);
    return [];
  }
}

// Generate summary with Claude, handling context window limits
async function generateSummaryWithClaude(dailyData, date) {
  try {
    // Calculate approximate token count for the data
    const dataText = dailyData.map(item => 
      `${item.timestamp}: ${item.summary || ''} ${item.extracted_text || ''} ${item.user_generated_text || ''}`
    ).join('\n');
    
    // Rough estimate: 1 token ≈ 4 characters
    const estimatedTokens = dataText.length / 4;
    const maxTokens = 150000; // Conservative limit for Claude
    
    console.log(`Estimated tokens: ${Math.round(estimatedTokens)}`);
    
    if (estimatedTokens > maxTokens) {
      console.log('Data too large for single summary. Generating hourly summaries first...');
      return await generateHourlySummariesThenDaily(dailyData, date);
    } else {
      console.log('Generating direct daily summary...');
      return await generateDirectDailySummary(dailyData, date);
    }
    
  } catch (error) {
    console.error('Error in generateSummaryWithClaude:', error.message);
    return null;
  }
}

// Generate hourly summaries first, then combine into daily summary
async function generateHourlySummariesThenDaily(dailyData, date) {
  try {
    console.log('Breaking down data into hourly chunks...');
    
    // Group data by hour
    const hourlyGroups = {};
    
    for (const item of dailyData) {
      const hour = new Date(item.timestamp).getHours();
      if (!hourlyGroups[hour]) {
        hourlyGroups[hour] = [];
      }
      hourlyGroups[hour].push(item);
    }
    
    console.log(`Found ${Object.keys(hourlyGroups).length} hours with data`);
    
    // Generate hourly summaries
    const hourlySummaries = [];
    
    for (const [hour, hourData] of Object.entries(hourlyGroups)) {
      console.log(`Generating summary for hour ${hour}:00...`);
      
      const hourSummary = await generateHourSummary(hourData, hour);
      if (hourSummary) {
        hourlySummaries.push({
          hour: parseInt(hour),
          summary: hourSummary,
          itemCount: hourData.length
        });
      }
    }
    
    console.log(`Generated ${hourlySummaries.length} hourly summaries`);
    
    // Combine hourly summaries into daily summary
    return await generateDailySummaryFromHourly(hourlySummaries, date);
    
  } catch (error) {
    console.error('Error in generateHourlySummariesThenDaily:', error.message);
    return null;
  }
}

// Generate summary for a single hour
async function generateHourSummary(hourData, hour) {
  try {
    const hourText = hourData.map(item => 
      `${item.timestamp}: App: ${item.active_app || 'Unknown'}, Summary: ${item.summary || ''}, Text: ${item.extracted_text || ''}, User Text: ${item.user_generated_text || ''}`
    ).join('\n');
    
    const response = await anthropic.messages.create({
      model: 'claude-3-7-sonnet-20250219',
      max_tokens: 2000,
      messages: [
        {
          role: 'user',
          content: `Please create a concise summary of the following hour of screen activity data (${hour}:00-${hour}:59). Focus on:
- Main applications used
- Key activities and tasks
- Any user-generated content (emails, messages, code, documents)
- Overall productivity patterns

Screen activity data:
${hourText}

Please provide a structured summary in markdown format.`
        }
      ]
    });
    
    return response.content[0].text;
    
  } catch (error) {
    console.error(`Error generating hour ${hour} summary:`, error.message);
    return null;
  }
}

// Generate daily summary from hourly summaries
async function generateDailySummaryFromHourly(hourlySummaries, date) {
  try {
    const hourlySummaryText = hourlySummaries.map(hour => 
      `## Hour ${hour.hour}:00-${hour.hour}:59 (${hour.itemCount} screenshots)\n${hour.summary}\n`
    ).join('\n');
    
    const response = await anthropic.messages.create({
      model: 'claude-3-7-sonnet-20250219',
      max_tokens: 4000,
      messages: [
        {
          role: 'user',
          content: `Please create a comprehensive daily summary for ${date} based on the following hourly summaries. 

Create a well-structured markdown document that includes:
1. **Executive Summary** - High-level overview of the day
2. **Key Activities** - Main tasks and work accomplished
3. **Applications Used** - Primary tools and software
4. **Productivity Insights** - Patterns and observations
5. **User-Generated Content** - Important communications, code, or documents created
6. **Time Distribution** - How time was spent across different activities
7. **Hourly Breakdown** - Detailed hour-by-hour activities

Hourly summaries:
${hourlySummaryText}

Please provide a comprehensive, well-formatted markdown summary.`
        }
      ]
    });
    
    return response.content[0].text;
    
  } catch (error) {
    console.error('Error generating daily summary from hourly:', error.message);
    return null;
  }
}

// Generate direct daily summary (when data fits in context window)
async function generateDirectDailySummary(dailyData, date) {
  try {
    const dailyText = dailyData.map(item => 
      `${item.timestamp}: App: ${item.active_app || 'Unknown'}, Summary: ${item.summary || ''}, Text: ${item.extracted_text || ''}, User Text: ${item.user_generated_text || ''}`
    ).join('\n');
    
    const response = await anthropic.messages.create({
      model: 'claude-3-7-sonnet-20250219',
      max_tokens: 4000,
      messages: [
        {
          role: 'user',
          content: `Please create a comprehensive daily summary for ${date} based on the following screen activity data from ${dailyData.length} screenshots.

Create a well-structured markdown document that includes:
1. **Executive Summary** - High-level overview of the day
2. **Key Activities** - Main tasks and work accomplished  
3. **Applications Used** - Primary tools and software
4. **Productivity Insights** - Patterns and observations
5. **User-Generated Content** - Important communications, code, or documents created
6. **Time Distribution** - How time was spent across different activities
7. **Timeline** - Key events and transitions throughout the day

Screen activity data:
${dailyText}

Please provide a comprehensive, well-formatted markdown summary.`
        }
      ]
    });
    
    return response.content[0].text;
    
  } catch (error) {
    console.error('Error generating direct daily summary:', error.message);
    return null;
  }
}

// Save summary to file
async function saveSummaryToFile(summary, date) {
  try {
    const filename = `${date}-summary.md`;
    const filePath = path.join(__dirname, filename);
    
    // Add header with metadata
    const fullContent = `# Daily Summary for ${date}

*Generated on: ${new Date().toISOString()}*

${summary}

---
*This summary was automatically generated from screen tracking data*
`;
    
    await fs.writeFile(filePath, fullContent, 'utf-8');
    console.log(`Summary saved to: ${filePath}`);
    
  } catch (error) {
    console.error('Error saving summary to file:', error.message);
  }
}