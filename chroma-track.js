import screenshot from 'screenshot-desktop';
import { createVectorStore, loadExistingHistoryToChroma } from './chroma-vector-store.js';

import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { Anthropic } from '@anthropic-ai/sdk';
import dotenv from 'dotenv';
// import { VectorStore } from 'vectorstore';
import readline from 'readline';
import { parse, format, startOfHour, endOfHour, startOfDay, endOfDay, isAfter, isBefore } from 'date-fns';
// import { pipeline } from '@xenova/transformers';

// Helper function to convert filename-style timestamps to ISO 8601
function convertFilenameTimestampToISO(ts) {
  if (typeof ts !== 'string') return ts; // Return as is if not a string

  // If it's already a valid ISO that Date can parse, and contains T, colons, and a period (or Z at the end)
  // This is a basic check; a more robust ISO validation could be used if needed.
  if (ts.includes('T') && ts.includes(':') && (ts.includes('.') || ts.endsWith('Z')) && !isNaN(new Date(ts).getTime())) {
    return ts; // Assume it's already in a good, parseable ISO format
  }

  // Expected input like: 2025-05-11T21-45-09-471Z
  // Desired output: 2025-05-11T21:45:09.471Z
  const parts = ts.split('T');
  if (parts.length !== 2) {
    // console.warn(`Timestamp ${ts} is not in expected YYYY-MM-DDTHH-MM-SS-FFFZ format for conversion.`);
    return ts; // Return original if not in expected parts
  }

  let timePart = parts[1];
  const zSuffix = timePart.endsWith('Z') ? 'Z' : '';
  if (zSuffix) {
    timePart = timePart.slice(0, -1); // Remove Z for processing
  }

  const timeSegments = timePart.split('-');
  if (timeSegments.length === 4) { // HH-MM-SS-FFF
    return `${parts[0]}T${timeSegments[0]}:${timeSegments[1]}:${timeSegments[2]}.${timeSegments[3]}${zSuffix}`;
  } else if (timeSegments.length === 3) { // HH-MM-SS (no milliseconds)
    return `${parts[0]}T${timeSegments[0]}:${timeSegments[1]}:${timeSegments[2]}${zSuffix}`;
  }

  // console.warn(`Timestamp ${ts} could not be converted to ISO format.`);
  return ts; // Fallback: return original if format is not matched
}

// Helper function for cosine similarity
function cosineSimilarity(vecA, vecB) {
  if (!vecA || !vecB || vecA.length !== vecB.length || vecA.length === 0) {
    // console.warn('Cosine similarity: Invalid vectors or zero length.', vecA, vecB);
    return 0;
  }
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  if (normA === 0 || normB === 0) {
    // console.warn('Cosine similarity: Zero norm vector.');
    return 0;
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// Self-contained InMemoryVectorStore class
class InMemoryVectorStore {
  constructor(embedderInstance) {
    if (!embedderInstance || typeof embedderInstance.embedQuery !== 'function' || typeof embedderInstance.embedDocuments !== 'function') {
        throw new Error('InMemoryVectorStore requires an embedder with embedQuery and embedDocuments methods.');
    }
    this.embedder = embedderInstance;
    this.vectors = []; // Stores { id, embedding, document, metadata }
    console.log('Custom InMemoryVectorStore initialized.');
  }

  async add(item) { // item: { id, document, metadata }
    try {
      // Using embedDocuments as it's generally robust for single/multiple items.
      // Ensure your embedder.embedDocuments returns an array of embeddings.
      const embeddings = await this.embedder.embedDocuments([item.document]);
      if (!embeddings || embeddings.length === 0 || !embeddings[0]) {
          console.error('Embedding failed or returned no result for document:', item.document);
          throw new Error('Embedding failed or returned no result.');
      }
      const embedding = embeddings[0];
      
      this.vectors.push({
        id: item.id,
        embedding: embedding,
        document: item.document,
        metadata: item.metadata,
      });
      // console.log(`InMemoryVectorStore: Added item ${item.id}`);
    } catch (error) {
      console.error(`InMemoryVectorStore add error for id ${item.id}:`, error.message, error.stack);
      // Depending on desired behavior, you might want to re-throw or handle more gracefully
    }
  }

  async query(queryOptions) { // queryOptions: { queryText, nResults, where (optional) }
    try {
      const queryEmbedding = await this.embedder.embedQuery(queryOptions.queryText);
      if (!queryEmbedding) {
          console.error('Query embedding failed for text:', queryOptions.queryText);
          throw new Error('Query embedding failed.');
      }

      const scoredVectors = this.vectors.map(vec => {
        if (!vec.embedding) {
            console.warn(`Vector with id ${vec.id} has no embedding. Skipping.`);
            return { ...vec, similarity: -1 }; // Or filter out later
        }
        return {
          ...vec,
          similarity: cosineSimilarity(queryEmbedding, vec.embedding),
        }
      }).filter(vec => vec.similarity > -1); // Filter out vectors that had no embedding

      scoredVectors.sort((a, b) => b.similarity - a.similarity);

      let results = scoredVectors;
      if (queryOptions.where && typeof queryOptions.where === 'function') {
        results = results.filter(vec => queryOptions.where(vec.metadata));
      }
      
      return results.slice(0, queryOptions.nResults || 5).map(vec => ({
        document: vec.document,
        metadata: vec.metadata,
        // similarity: vec.similarity // Optional: useful for debugging
      }));
    } catch (error) {
      console.error('InMemoryVectorStore query error:', error.message, error.stack);
      return []; // Return empty array on error
    }
  }
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

// Initialize vector store (in-memory)
// let vectorStore;
// Initialize vector store (in-memory)
let vectorStore; // Keep this global variable
async function initializeVectorStore() {
  try {
    // Always use simple Chroma store for now
    console.log('Initializing Simple Chroma store...');
    const chromaOptions = {
      collectionName: 'screen_history',
      serverUrl: process.env.CHROMA_SERVER_URL || 'http://localhost:8000'
    };
    vectorStore = await createSimpleChromaStore(chromaOptions.collectionName, chromaOptions.serverUrl);
    console.log('Simple Chroma store initialized successfully');
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

// Get current timestamp in ISO format (for filenames)
function getTimestampForFilename() {
  return new Date().toISOString().replace(/[:.]/g, '-');
}

// Process screenshot with Claude - UPDATED to include user_generated_text detection
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

// Add JSON data to vector store
async function addToVectorStore(collection, analysisData) { // analysisData should have analysisData.timestamp as ISO
  try {
    const textToEmbed = `${analysisData.summary} ${analysisData.extracted_text}`;
    
    // Ensure analysisData.timestamp is a valid ISO string
    if (!analysisData.timestamp || isNaN(new Date(analysisData.timestamp).getTime())) {
      console.error(`Invalid or missing timestamp in analysisData for addToVectorStore. Timestamp: ${analysisData.timestamp}. Data:`, analysisData);
      return; 
    }

    await collection.add({
      id: analysisData.timestamp, // Use the ISO timestamp from analysisData as ID
      document: textToEmbed,
      metadata: { ...analysisData }, // analysisData itself becomes metadata, includes its .timestamp
    });
    // console.log(`Added to vector store (ID: ${analysisData.timestamp})`);
  } catch (error) {
    // console.error(`Vector store add error for ID ${analysisData.timestamp}:`, error.message);
  }
}

// Parse natural language time references (existing simple parser)
function parseTimeQuery(queryText) {
  const now = new Date();
  let startTime, endTime;

  if (queryText.toLowerCase().includes('yesterday')) {
    startTime = new Date(now);
    startTime.setDate(now.getDate() - 1);
    startTime.setHours(0, 0, 0, 0);
    endTime = new Date(now);
    endTime.setDate(now.getDate() - 1);
    endTime.setHours(23, 59, 59, 999);
  } else if (queryText.match(/\d{4}-\d{2}-\d{2}/)) {
    const dateStr = queryText.match(/\d{4}-\d{2}-\d{2}/)[0];
    try {
        // Attempt to parse with date-fns, assuming the matched string is the date
        startTime = parse(dateStr, 'yyyy-MM-dd', new Date());
        startTime.setHours(0, 0, 0, 0);
        endTime = new Date(startTime);
        endTime.setHours(23, 59, 59, 999);
    } catch (e) {
        console.warn(`Could not parse date string: ${dateStr} with date-fns. Falling back or skipping.`);
        return null;
    }
  } else {
    return null;
  }

  return {
    start: startTime.toISOString(),
    end: endTime.toISOString(),
  };
}

// New function to parse natural language time with Claude
async function parseNaturalLanguageTimeWithClaude(queryText) {
  try {
    const currentISODate = new Date().toISOString();
    const prompt = `Given the user's query: "${queryText}"

Analyze this query to identify any specific dates, date ranges, or relative time references (like "today", "yesterday", "last Tuesday", "this week", "last month", "between May 1st and May 5th").

If a time reference is found, provide the start and end of that time range in ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ).

For "today", the range is from the beginning of today to the end of today.
For "yesterday", from the beginning of yesterday to the end of yesterday.
For "this week", assume the week starts on Monday, provide the range from the beginning of this Monday to the end of this coming Sunday.
For "last month", provide the range for the entire previous calendar month.
If a single date is mentioned (e.g., "on May 10th"), provide the range for that entire day.
If an open-ended range like "since Monday" is mentioned, use the current time as the end of the range.
If no specific time reference is found, or if it's too vague, output null for startTimeISO and endTimeISO.

Current date for reference: ${currentISODate}

Output ONLY the JSON object like this:
{
"startTimeISO": "YYYY-MM-DDTHH:mm:ss.sssZ_or_null",
"endTimeISO": "YYYY-MM-DDTHH:mm:ss.sssZ_or_null",
"cleanedQuery": "The user query with the time phrases removed or normalized, focusing on the core activity."
}
If no time is found, both startTimeISO and endTimeISO should be null, and cleanedQuery should be the original query.`;

    console.log("Requesting time parsing from Claude for query:", queryText);
    const response = await anthropic.messages.create({
      model: 'claude-3-opus-20240229',
      max_tokens: 300,
      messages: [{ role: 'user', content: prompt }],
    });

    const resultText = response.content[0].text.trim();
    console.log("Claude time parsing raw response:", resultText);
    
    try {
        const cleanedJsonString = resultText.replace(/^```json\s*|```$/g, '');
        const parsedResult = JSON.parse(cleanedJsonString);
        
        console.log("Claude parsed time and query:", parsedResult);

        if (parsedResult && parsedResult.cleanedQuery) {
            if ((parsedResult.startTimeISO && !parsedResult.endTimeISO) || (!parsedResult.startTimeISO && parsedResult.endTimeISO)) {
                console.warn("Claude returned partial time range, ignoring time filter for safety:", parsedResult);
                return { start: null, end: null, cleanedQuery: queryText };
            }
            
            const isValidISODate = (isoString) => {
                if (!isoString) return true;
                return !isNaN(new Date(isoString).getTime());
            };

            if (!isValidISODate(parsedResult.startTimeISO) || !isValidISODate(parsedResult.endTimeISO)) {
                console.warn("Claude returned invalid ISO date format, ignoring time filter:", parsedResult);
                return { start: null, end: null, cleanedQuery: queryText };
            }

            return {
                start: parsedResult.startTimeISO || null,
                end: parsedResult.endTimeISO || null,
                cleanedQuery: parsedResult.cleanedQuery || queryText
            };
        } else {
            console.warn("Claude response for time parsing did not contain cleanedQuery or was not as expected:", parsedResult);
        }
    } catch (e) {
      console.error('Error parsing time extraction response from Claude:', e, "Raw response:", resultText);
    }
  } catch (error) {
    console.error('Claude API Error during time parsing:', error.message);
  }
  
  console.log("Falling back to original query due to Claude time parsing issue.");
  return { start: null, end: null, cleanedQuery: queryText };
}

// Query vector store and generate response with Claude - UPDATED
async function queryVectorStore(collection, originalQueryText) {
  try {
    console.log(`Original user query: "${originalQueryText}"`);
    
    // Route the query first
    const routeResult = await routeQuery(originalQueryText);
    
    // If it's not a search query, handle it with the appropriate method
    if (routeResult.query_type !== 'SEARCH') {
      return await handleRoutedQuery(collection, routeResult, originalQueryText);
    }
    
    // Continue with existing search logic for SEARCH queries
    const timeParseResult = await parseNaturalLanguageTimeWithClaude(originalQueryText);
    
    let timeFilter = null;
    if (timeParseResult && timeParseResult.start && timeParseResult.end) {
      const startDate = new Date(timeParseResult.start);
      const endDate = new Date(timeParseResult.end);
      if (!isNaN(startDate.getTime()) && !isNaN(endDate.getTime())) {
        timeFilter = {
          start: startDate.toISOString(),
          end: endDate.toISOString(),
        };
      } else {
        console.warn(`Invalid date strings from Claude: start='${timeParseResult.start}', end='${timeParseResult.end}'. Proceeding without time filter.`);
      }
    }
    
    let queryForEmbedding = (timeParseResult && timeParseResult.cleanedQuery) ? timeParseResult.cleanedQuery : originalQueryText;
    if (!queryForEmbedding.trim()) {
        queryForEmbedding = 'What was I doing?';
    }

    console.log(`Executing vector query with: Cleaned Query='${queryForEmbedding}', StartTime='${timeFilter ? timeFilter.start : 'N/A'}', EndTime='${timeFilter ? timeFilter.end : 'N/A'}'`);

    let results;
    if (timeFilter) {
      results = await collection.query({
        queryText: queryForEmbedding,
        nResults: 10,
        where: (metadata) => {
          if (!metadata.timestamp) return false;
          try {
            const metadataTimestamp = new Date(metadata.timestamp).toISOString();
            return metadataTimestamp >= timeFilter.start && metadataTimestamp <= timeFilter.end;
          } catch (e) {
            console.warn(`Could not parse metadata.timestamp: ${metadata.timestamp}`);
            return false;
          }
        }
      });
    } else {
      const simpleTimeFilter = parseTimeQuery(originalQueryText); 
      if (simpleTimeFilter) {
        console.log("Using fallback simple time parser. Filter:", simpleTimeFilter);
        let fallbackQueryForEmbedding = originalQueryText
            .replace(/yesterday/gi, '') 
            .replace(/\d{4}-\d{2}-\d{2}/, '') 
            .trim();
        if (!fallbackQueryForEmbedding) fallbackQueryForEmbedding = 'What was I doing?';
        
        console.log(`Executing vector query with (fallback time filter): Cleaned Query='${fallbackQueryForEmbedding}', StartTime='${simpleTimeFilter.start}', EndTime='${simpleTimeFilter.end}'`);
        results = await collection.query({
            queryText: fallbackQueryForEmbedding,
            nResults: 5,
            where: (metadata) => {
                if (!metadata.timestamp) return false;
                 try {
                    const metadataTimestamp = new Date(metadata.timestamp).toISOString();
                    return metadataTimestamp >= simpleTimeFilter.start && metadataTimestamp <= simpleTimeFilter.end;
                } catch (e) {
                    console.warn(`Could not parse metadata.timestamp: ${metadata.timestamp}`);
                    return false;
                }
            }
        });
      } else {
        console.log(`Executing vector query with: Cleaned Query='${queryForEmbedding}' (no time filter)`);
        results = await collection.query({
            queryText: queryForEmbedding,
            nResults: 5,
        });
      }
    }

    const context = results.map((result) => ({
      document: result.document,
      metadata: result.metadata,
    }));

    console.log('Retrieved context from vector store (RAG results):', JSON.stringify(context, null, 2));

    if (context.length === 0) {
        return "I couldn't find any activity matching your query and time range.";
    }

    const promptForClaudeSummary = `Based on the following context, answer the query: "${originalQueryText}"

Context:
${context.map((c, i) => `Document ${i + 1}: ${c.document} (Timestamp: ${c.metadata.timestamp})`).join('\n')}

Answer in a concise, natural language format. If the query asks for a summary of activities, provide that.`;
    
    console.log("Sending context to Claude for final summarization. Original query:", originalQueryText);
    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620', 
      max_tokens: 500,
      messages: [{ role: 'user', content: promptForClaudeSummary }],
    });

    return response.content[0].text;

  } catch (error) {
    console.error('Query error in queryVectorStore:', error.message, error.stack);
    return 'Error processing query.';
  }
}

// Terminal query interface
function startQueryInterface(collection) {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  rl.setPrompt('Query> ');
  rl.prompt();

  rl.on('line', async (line) => {
    if (line.trim().toLowerCase() === 'exit') {
      rl.close();
      return;
    }

    console.log('Processing query:', line);
    
    // Check if this is a communication style query
    if (line.toLowerCase().includes('respond like me') || 
        line.toLowerCase().includes('communication style') ||
        line.toLowerCase().includes('how would i respond')) {
      const response = await handleCommunicationStyleQuery(collection, line);
      console.log('Response:', response);
    } else {
      const response = await queryVectorStore(collection, line);
      console.log('Response:', response);
    }
    
    rl.prompt();
  });

  rl.on('close', () => {
    console.log('Query interface closed.');
    process.exit(0);
  });
}

// Handle communication style queries
async function handleCommunicationStyleQuery(collection, queryText) {
  try {
    // First, get relevant context from vector search
    const contextResponse = await queryVectorStore(collection, queryText);
    
    // Then, get the user's communication style
    const automationsDir = path.join(__dirname, 'automations');
    const styleFile = path.join(automationsDir, 'user_communication_style.md');
    
    let communicationStyle = '';
    try {
      communicationStyle = await fs.readFile(styleFile, 'utf-8');
    } catch (err) {
      communicationStyle = 'No communication style data available yet.';
    }
    
    const prompt = `Based on the user's communication style and relevant context, respond to this query as the user would:

Query: "${queryText}"

Relevant Context:
${contextResponse}

User Communication Style:
${communicationStyle}

Instructions:
1. Use the user's typical tone, vocabulary, and communication patterns
2. Include relevant information from the context
3. Respond as if you are the user answering this question
4. Match the user's typical response length and style`;

    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 800,
      messages: [{ role: 'user', content: prompt }]
    });
    
    return response.content[0].text;
  } catch (error) {
    console.error('Error handling communication style query:', error);
    return 'Error processing communication style query.';
  }
}

// Add this function or integrate its logic into trackScreen

async function loadExistingHistory(collection, screenhistoryDir) {
  const vectorStoreType = process.env.VECTOR_STORE_TYPE || 'simple-chroma';
  
  if (vectorStoreType === 'simple-chroma') {
    // Use simple loading for simple Chroma store
    await loadExistingHistorySimple(collection, screenhistoryDir);
  } else if (vectorStoreType === 'chroma') {
    // Use the in-memory loading function as fallback
    await loadExistingHistoryInMemory(collection, screenhistoryDir);
  } else {
    // Use your existing loading logic for in-memory store
    await loadExistingHistoryInMemory(collection, screenhistoryDir);
  }
}

// Simple loading function for simple Chroma store
async function loadExistingHistorySimple(collection, screenhistoryDir) {
  console.log('Starting to load existing screen history into Simple Chroma store...');
  const startTime = Date.now();
  
  try {
    const files = await fs.readdir(screenhistoryDir);
    const jsonFiles = files.filter(file => path.extname(file).toLowerCase() === '.json');
    console.log(`Found ${jsonFiles.length} JSON files to process`);

    const batchSize = 100; // Process in batches for better performance
    let processedCount = 0;
    let currentBatch = [];
    
    // Remove the test limit: process all files
    const filesToProcess = jsonFiles;
    
    for (const file of filesToProcess) {
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
            // If get fails, assume it doesn't exist
            exists = false;
          }
          if (exists) {
            // console.log(`Skipping already indexed file: ${file}`);
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
              const remaining = filesToProcess.length - processedCount;
              const estimatedTimeRemaining = remaining / rate / 60;
              const currentTimestamp = new Date().toISOString();

              console.log(`[${currentTimestamp}] Progress: ${processedCount}/${filesToProcess.length} files processed. Estimated time remaining: ${estimatedTimeRemaining.toFixed(1)} minutes`);
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
    console.log(`Finished loading ${processedCount} files into Simple Chroma store in ${totalTime.toFixed(1)} seconds`);
    
    // Display stats
    const stats = await collection.getStats();
    console.log(`Simple Chroma collection stats:`, stats);
    
  } catch (err) {
    console.error(`Error reading screenhistory directory: ${err.message}`);
  }
}

// Rename your existing loadExistingHistory to this:
async function loadExistingHistoryInMemory(collection, screenhistoryDir) {
  console.log('Starting to load existing screen history into memory...');
  const startTime = Date.now();
  
  try {
    const files = await fs.readdir(screenhistoryDir);
    const jsonFiles = files.filter(file => path.extname(file).toLowerCase() === '.json');
    console.log(`Found ${jsonFiles.length} JSON files to process`);

    let processedCount = 0;
    for (const file of jsonFiles) {
      const filePath = path.join(screenhistoryDir, file);
      try {
        const fileContent = await fs.readFile(filePath, 'utf-8');
        let analysis = null;
        
        if (fileContent.trim() === 'null' || fileContent.trim() === '') {
          analysis = null;
        } else {
          try {
            analysis = JSON.parse(fileContent);
          } catch (parseError) {
            console.warn(`Skipping ${file}: Could not parse JSON. Error: ${parseError.message}`);
            analysis = null;
          }
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
          await addToVectorStore(collection, analysis);
        }
        
        processedCount++;
        
        // Progress logging every 100 files
        if (processedCount % 100 === 0) {
          const elapsed = Date.now() - startTime;
          const rate = processedCount / elapsed * 1000;
          const remaining = jsonFiles.length - processedCount;
          const estimatedTimeRemaining = remaining / rate / 60;
          const currentTimestamp = new Date().toISOString();

          console.log(`[${currentTimestamp}] Progress: ${processedCount}/${jsonFiles.length} files processed. Estimated time remaining: ${estimatedTimeRemaining.toFixed(1)} minutes`);
        }
        
      } catch (err) {
        console.error(`Error processing history file ${file}: ${err.message}`);
      }
    }
    
    const totalTime = (Date.now() - startTime) / 1000;
    console.log(`Finished loading ${processedCount} files in ${totalTime.toFixed(1)} seconds`);
  } catch (err) {
    console.error(`Error reading screenhistory directory: ${err.message}`);
  }
}

// Generate hourly summary
async function generateHourlySummary(collection, hour) {
  try {
    const startTime = startOfHour(hour).toISOString();
    const endTime = endOfHour(hour).toISOString();
    
    console.log(`Generating hourly summary for ${format(hour, 'HH:mm')} on ${format(hour, 'yyyy-MM-dd')}`);
    
    const results = await collection.query({
      queryText: "What activities and tasks were completed",
      nResults: 50,
      where: (metadata) => {
        if (!metadata.timestamp) return false;
        try {
          const metadataTimestamp = new Date(metadata.timestamp).toISOString();
          return metadataTimestamp >= startTime && metadataTimestamp <= endTime;
        } catch (e) {
          return false;
        }
      }
    });

    if (results.length === 0) {
      return null; // No activity this hour
    }

    const context = results.map(r => r.metadata).filter(m => m);
    const apps = [...new Set(context.map(c => c.active_app).filter(Boolean))];
    const categories = [...new Set(context.map(c => c.task_category).filter(Boolean))];
    const avgProductivity = context.length > 0 ? 
      context.reduce((sum, c) => sum + (c.productivity_score || 0), 0) / context.length : 0;

    const prompt = `Analyze this hour of activity and create a concise summary:

Time Period: ${format(hour, 'HH:mm')} on ${format(hour, 'yyyy-MM-dd')}
Activities: ${context.map(c => c.summary).join('; ')}
Apps Used: ${apps.join(', ')}
Task Categories: ${categories.join(', ')}

Provide a summary in this JSON format:
{
  "active_app": "Primary app used",
  "summary": "Concise description of what was accomplished this hour",
  "extracted_text": "Key text/content worked with",
  "task_category": "Primary task category",
  "productivity_score": ${Math.round(avgProductivity)},
  "workflow_suggestions": "Brief suggestions for improvement"
}`;

    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 800,
      messages: [{ role: 'user', content: prompt }]
    });

    const cleanedResponse = response.content[0].text
      .replace(/```json\n?/g, '')
      .replace(/```\n?/g, '')
      .trim();
    
    const summary = JSON.parse(cleanedResponse);
    summary.timestamp = startTime;
    summary.period_type = "hourly";
    summary.period_start = startTime;
    summary.period_end = endTime;
    
    return summary;
  } catch (error) {
    console.error('Error generating hourly summary:', error);
    return null;
  }
}

// Generate daily summary
async function generateDailySummary(date) {
  try {
    const dateStr = format(date, 'dd-MMM-yyyy').toLowerCase();
    const hourlySummariesDir = path.join(__dirname, 'hourly-summaries');
    
    console.log(`Generating daily summary for ${format(date, 'yyyy-MM-dd')}`);
    
    // Read all hourly summaries for this day
    const files = await fs.readdir(hourlySummariesDir).catch(() => []);
    const dayFiles = files.filter(file => file.includes(dateStr));
    
    const hourlySummaries = [];
    for (const file of dayFiles) {
      try {
        const content = await fs.readFile(path.join(hourlySummariesDir, file), 'utf-8');
        const summary = JSON.parse(content);
        hourlySummaries.push(summary);
      } catch (err) {
        console.warn(`Could not read hourly summary ${file}:`, err.message);
      }
    }

    if (hourlySummaries.length === 0) {
      return null;
    }

    const apps = [...new Set(hourlySummaries.map(s => s.active_app).filter(Boolean))];
    const categories = [...new Set(hourlySummaries.map(s => s.task_category).filter(Boolean))];
    const avgProductivity = hourlySummaries.reduce((sum, s) => sum + (s.productivity_score || 0), 0) / hourlySummaries.length;

    const prompt = `Create a daily summary from these hourly summaries:

Date: ${format(date, 'yyyy-MM-dd')}
Hourly Activities:
${hourlySummaries.map((s, i) => `Hour ${i + 1}: ${s.summary}`).join('\n')}

Apps Used: ${apps.join(', ')}
Task Categories: ${categories.join(', ')}

Provide a comprehensive daily summary in this JSON format:
{
  "active_app": "Most used app",
  "summary": "Comprehensive summary of the day's work and accomplishments",
  "extracted_text": "Key outcomes, decisions, or important content from the day",
  "task_category": "Primary focus area",
  "productivity_score": ${Math.round(avgProductivity)},
  "workflow_suggestions": "Suggestions for tomorrow or process improvements"
}`;

    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 1200,
      messages: [{ role: 'user', content: prompt }]
    });

    const cleanedResponse = response.content[0].text
      .replace(/```json\n?/g, '')
      .replace(/```\n?/g, '')
      .trim();
    
    const summary = JSON.parse(cleanedResponse);
    summary.timestamp = startOfDay(date).toISOString();
    summary.period_type = "daily";
    summary.period_start = startOfDay(date).toISOString();
    summary.period_end = endOfDay(date).toISOString();
    
    return summary;
  } catch (error) {
    console.error('Error generating daily summary:', error);
    return null;
  }
}

// Save summary to appropriate directory
async function saveSummary(summary, type) {
  try {
    const summariesDir = path.join(__dirname, `${type}-summaries`);
    await fs.mkdir(summariesDir, { recursive: true });
    
    const date = new Date(summary.timestamp);
    let filename;
    
    if (type === 'hourly') {
      filename = `${format(date, 'HH')}-${format(date, 'dd-MMM-yyyy').toLowerCase()}.json`;
    } else if (type === 'daily') {
      filename = `${format(date, 'dd-MMM-yyyy').toLowerCase()}.json`;
    }
    
    const filepath = path.join(summariesDir, filename);
    await fs.writeFile(filepath, JSON.stringify(summary, null, 2));
    console.log(`${type} summary saved to ${filepath}`);
  } catch (error) {
    console.error(`Error saving ${type} summary:`, error);
  }
}

// Intelligent query router
async function routeQuery(queryText) {
  try {
    const prompt = `Analyze this user query and determine the best way to handle it:

Query: "${queryText}"

Classify this query into one of these types and extract relevant parameters:

1. SEARCH - For specific information, URLs, files, or detailed content from screenshots
2. WEEKLY_SUMMARY - For weekly summaries or broad time periods (weeks/months)  
3. DAILY_SUMMARY - For daily summaries or questions about specific days
4. HOURLY_SUMMARY - For hourly summaries or questions about specific hours

Output ONLY this JSON format:
{
  "query_type": "SEARCH|WEEKLY_SUMMARY|DAILY_SUMMARY|HOURLY_SUMMARY",
  "time_period": "specific date/time if mentioned, null otherwise",
  "cleaned_query": "query with time references removed, focusing on core content"
}`;

    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 300,
      messages: [{ role: 'user', content: prompt }]
    });

    const cleanedResponse = response.content[0].text
      .replace(/```json\n?/g, '')
      .replace(/```\n?/g, '')
      .trim();
    
    return JSON.parse(cleanedResponse);
  } catch (error) {
    console.error('Error routing query:', error);
    return { query_type: "SEARCH", time_period: null, cleaned_query: queryText };
  }
}

// Handle different query types
async function handleRoutedQuery(collection, routeResult, originalQuery) {
  const { query_type, time_period, cleaned_query } = routeResult;
  
  console.log(`Handling ${query_type} query: "${cleaned_query}"`);
  
  switch (query_type) {
    case 'SEARCH':
      return await queryVectorStore(collection, originalQuery);
      
    case 'HOURLY_SUMMARY':
      return await queryHourlySummaries(cleaned_query, time_period);
      
    case 'DAILY_SUMMARY':
      return await queryDailySummaries(cleaned_query, time_period);
      
    case 'WEEKLY_SUMMARY':
      return await queryWeeklySummaries(cleaned_query, time_period);
      
    default:
      return await queryVectorStore(collection, originalQuery);
  }
}

// Query hourly summaries
async function queryHourlySummaries(queryText, timePeriod) {
  try {
    const hourlySummariesDir = path.join(__dirname, 'hourly-summaries');
    const files = await fs.readdir(hourlySummariesDir).catch(() => []);
    
    const summaries = [];
    for (const file of files) {
      try {
        const content = await fs.readFile(path.join(hourlySummariesDir, file), 'utf-8');
        summaries.push(JSON.parse(content));
      } catch (err) {
        continue;
      }
    }
    
    const context = summaries.map(s => 
      `${s.timestamp}: ${s.summary} (${s.task_category})`
    ).join('\n');
    
    const prompt = `Based on these hourly summaries, answer: "${queryText}"

Hourly Summaries:
${context}

Provide a natural language response.`;
    
    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 600,
      messages: [{ role: 'user', content: prompt }]
    });
    
    return response.content[0].text;
  } catch (error) {
    console.error('Error querying hourly summaries:', error);
    return 'Error retrieving hourly summaries.';
  }
}

// Query daily summaries  
async function queryDailySummaries(queryText, timePeriod) {
  try {
    const dailySummariesDir = path.join(__dirname, 'daily-summaries');
    const files = await fs.readdir(dailySummariesDir).catch(() => []);
    
    const summaries = [];
    for (const file of files) {
      try {
        const content = await fs.readFile(path.join(dailySummariesDir, file), 'utf-8');
        summaries.push(JSON.parse(content));
      } catch (err) {
        continue;
      }
    }
    
    const context = summaries.map(s => 
      `${format(new Date(s.timestamp), 'yyyy-MM-dd')}: ${s.summary}`
    ).join('\n');
    
    const prompt = `Based on these daily summaries, answer: "${queryText}"

Daily Summaries:
${context}

Provide a natural language response.`;
    
    const response = await anthropic.messages.create({
      model: 'claude-3-5-sonnet-20240620',
      max_tokens: 800,
      messages: [{ role: 'user', content: prompt }]
    });
    
    return response.content[0].text;
  } catch (error) {
    console.error('Error querying daily summaries:', error);
    return 'Error retrieving daily summaries.';
  }
}

// Query weekly summaries (uses daily summaries)
async function queryWeeklySummaries(queryText, timePeriod) {
  // For now, use daily summaries to answer weekly questions
  return await queryDailySummaries(queryText, timePeriod);
}



// Main tracking function
async function trackScreen() {
  try {
    console.log('Starting screen tracking...');
    const { screenshotsDir, screenhistoryDir } = await ensureDirectories();
    const collection = await initializeVectorStore();

    if (!collection) {
      throw new Error('Failed to initialize vector store');
    }

    await loadExistingHistory(collection, screenhistoryDir);

    // Start query interface in parallel
    startQueryInterface(collection);

    let lastHourlyCheck = new Date();
    let lastDailyCheck = new Date();

    // Main loop for capturing new screenshots
    while (true) {
      const now = new Date();
      const currentISOTimestamp = now.toISOString();
      const filenameTimestamp = currentISOTimestamp.replace(/[:.]/g, '-');

      // Check for hourly summary generation
      if (now.getMinutes() === 0 && now.getTime() - lastHourlyCheck.getTime() > 50 * 60 * 1000) {
        const lastHour = new Date(now.getTime() - 60 * 60 * 1000);
        const hourlySummary = await generateHourlySummary(collection, lastHour);
        if (hourlySummary) {
          await saveSummary(hourlySummary, 'hourly');
        }
        lastHourlyCheck = now;
      }

      // Check for daily summary generation (at 5 PM)
      if (now.getHours() === 17 && now.getMinutes() === 0 && 
          now.getTime() - lastDailyCheck.getTime() > 20 * 60 * 60 * 1000) {
        const yesterday = new Date(now.getTime() - 24 * 60 * 60 * 1000);
        const dailySummary = await generateDailySummary(yesterday);
        if (dailySummary) {
          await saveSummary(dailySummary, 'daily');
        }
        lastDailyCheck = now;
      }

      const screenshotPath = path.join(screenshotsDir, `${filenameTimestamp}.jpg`);
      const jsonPath = path.join(screenhistoryDir, `${filenameTimestamp}.json`);
      
      const img = await screenshot();
      await fs.writeFile(screenshotPath, img);
      
      const base64Image = bufferToBase64(img);
      const analysis = await processScreenshotWithClaude(base64Image);
      
      if (analysis) {
        analysis.timestamp = currentISOTimestamp;
        await fs.writeFile(jsonPath, JSON.stringify(analysis, null, 2));
        await addToVectorStore(collection, analysis);
        
        // Update communication style if user_generated_text exists
        if (analysis.user_generated_text && analysis.active_app) {
          await updateUserCommunicationStyle(analysis.user_generated_text, analysis.active_app);
        }
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
console.log(`Script boot time: ${new Date().toISOString()}`); // Boot time logging
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
      // Get or create collection
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

  async add(item) { // item: { id, document, metadata }
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized. Call initialize() first.');
      }

      // Create metadata with all relevant fields
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

      // Use upsert to avoid duplicates
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

  async addBatch(items) { // items: Array of { id, document, metadata }
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

  async query(queryOptions) { // queryOptions: { queryText, nResults, where (optional) }
    try {
      if (!this.collection) {
        throw new Error('SimpleChromaStore not initialized. Call initialize() first.');
      }

      // Let ChromaDB handle the embedding and querying
      const results = await this.collection.query({
        queryTexts: [queryOptions.queryText],
        nResults: queryOptions.nResults || 5
      });

      // Convert results to match existing interface
      let formattedResults = this.formatResults(results);
      
      // Apply where filtering after query if needed
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
    
    // Create Chroma client
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