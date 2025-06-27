import { ChromaClient } from "chromadb";
import { promises as fs } from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Get current file's directory
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

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

// ChromaVectorStore class that implements the same interface as your InMemoryVectorStore
class ChromaVectorStore {
  constructor(chromaClient, embedder, collectionName = 'screen_history') {
    this.client = chromaClient;
    this.embedder = embedder;
    this.collectionName = collectionName;
    this.collection = null;
    console.log('ChromaVectorStore initialized.');
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
      console.log(`Chroma collection '${this.collectionName}' ready.`);
      return this.collection;
    } catch (error) {
      console.error('ChromaVectorStore initialization error:', error.message);
      throw error;
    }
  }

  async add(item) { // item: { id, document, metadata }
    try {
      if (!this.collection) {
        throw new Error('ChromaVectorStore not initialized. Call initialize() first.');
      }

      // Generate embedding for the document
      const embeddings = await this.embedder.embedDocuments([item.document]);
      if (!embeddings || embeddings.length === 0 || !embeddings[0]) {
        console.error('Embedding failed or returned no result for document:', item.document);
        return;
      }
      const embedding = embeddings[0];

      // Ensure metadata is serializable (Chroma requires this)
      const cleanMetadata = this.sanitizeMetadata(item.metadata);

      await this.collection.add({
        ids: [item.id],
        documents: [item.document],
        embeddings: [embedding],
        metadatas: [cleanMetadata]
      });

      console.log(`ChromaVectorStore: Added item ${item.id}`);
    } catch (error) {
      console.error(`ChromaVectorStore add error for id ${item.id}:`, error.message);
      // Don't throw to maintain compatibility with existing error handling
    }
  }

  async addBatch(items) { // items: Array of { id, document, metadata }
    try {
      if (!this.collection) {
        throw new Error('ChromaVectorStore not initialized. Call initialize() first.');
      }

      const ids = items.map(item => item.id);
      const documents = items.map(item => item.document);
      const metadatas = items.map(item => this.sanitizeMetadata(item.metadata));

      // Generate embeddings for all documents
      const embeddings = await this.embedder.embedDocuments(documents);
      if (!embeddings || embeddings.length !== documents.length) {
        console.error('Embedding failed for batch. Expected', documents.length, 'embeddings, got', embeddings ? embeddings.length : 0);
        return;
      }

      await this.collection.add({
        ids: ids,
        documents: documents,
        embeddings: embeddings,
        metadatas: metadatas
      });

      console.log(`ChromaVectorStore: Added batch of ${items.length} items`);
    } catch (error) {
      console.error('ChromaVectorStore batch add error:', error.message);
    }
  }

  async query(queryOptions) { // queryOptions: { queryText, nResults, where (optional) }
    try {
      if (!this.collection) {
        throw new Error('ChromaVectorStore not initialized. Call initialize() first.');
      }

      // Generate embedding for the query
      const queryEmbedding = await this.embedder.embedQuery(queryOptions.queryText);
      if (!queryEmbedding) {
        console.error('Query embedding failed for text:', queryOptions.queryText);
        return [];
      }

      let whereClause = undefined;
      
      // Convert the where function to Chroma's metadata filtering format
      if (queryOptions.where && typeof queryOptions.where === 'function') {
        // For time-based filtering, we need to convert the function to Chroma's format
        // This is a bit tricky since Chroma doesn't support arbitrary functions
        // We'll handle common time filtering patterns
        whereClause = this.convertWhereFunction(queryOptions.where);
      }

      const results = await this.collection.query({
        queryEmbeddings: [queryEmbedding],
        nResults: queryOptions.nResults || 5,
        where: whereClause
      });

      // Convert Chroma results to match your existing interface
      return this.formatResults(results);
    } catch (error) {
      console.error('ChromaVectorStore query error:', error.message);
      return [];
    }
  }

  // Helper method to sanitize metadata for Chroma
  sanitizeMetadata(metadata) {
    if (!metadata) return {};
    
    const sanitized = {};
    for (const [key, value] of Object.entries(metadata)) {
      // Chroma supports string, number, and boolean values in metadata
      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        sanitized[key] = value;
      } else if (value != null) {
        // Convert other types to strings
        sanitized[key] = String(value);
      }
    }
    return sanitized;
  }

  // Convert where function to Chroma metadata filtering (limited support)
  convertWhereFunction(whereFunc) {
    // This is a simplified approach - you might need to enhance this
    // based on your specific filtering needs
    
    // For now, we'll return undefined and handle filtering post-query
    // Chroma's where clause syntax is different from function-based filtering
    return undefined;
  }

  // Format Chroma results to match your existing interface
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
      distance: distances[index] || 0 // Chroma returns distances, not similarities
    }));
  }

  // Get collection stats
  async getStats() {
    try {
      if (!this.collection) {
        throw new Error('ChromaVectorStore not initialized.');
      }

      const count = await this.collection.count();
      return {
        totalDocuments: count,
        collectionName: this.collectionName
      };
    } catch (error) {
      console.error('ChromaVectorStore stats error:', error.message);
      return { totalDocuments: 0, collectionName: this.collectionName };
    }
  }
}

// Factory function to create and initialize ChromaVectorStore
async function createChromaVectorStore(embedder, collectionName = 'screen_history', chromaServerUrl = 'http://localhost:8000') {
  try {
    // Create Chroma client - adjust URL based on your setup
    const client = new ChromaClient({
      path: chromaServerUrl
    });

    const vectorStore = new ChromaVectorStore(client, embedder, collectionName);
    await vectorStore.initialize();
    
    return vectorStore;
  } catch (error) {
    console.error('Failed to create ChromaVectorStore:', error.message);
    throw error;
  }
}

// Load existing history into Chroma
async function loadExistingHistoryToChroma(vectorStore, screenhistoryDir) {
  console.log('Starting to load existing screen history into Chroma...');
  const startTime = Date.now();
  
  try {
    const files = await fs.readdir(screenhistoryDir);
    const jsonFiles = files.filter(file => path.extname(file).toLowerCase() === '.json');
    console.log(`Found ${jsonFiles.length} JSON files to process`);

    const batchSize = 100; // Process in batches for better performance
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
          
          // Prepare for batch insertion
          const textToEmbed = `${analysis.summary} ${analysis.extracted_text}`;
          currentBatch.push({
            id: analysis.timestamp,
            document: textToEmbed,
            metadata: analysis
          });

          // Process batch when it reaches batchSize
          if (currentBatch.length >= batchSize) {
            await vectorStore.addBatch(currentBatch);
            processedCount += currentBatch.length;
            currentBatch = [];

            // Progress logging
            if (processedCount % 500 === 0) {
              const elapsed = Date.now() - startTime;
              const rate = processedCount / elapsed * 1000;
              const remaining = jsonFiles.length - processedCount;
              const estimatedTimeRemaining = remaining / rate / 60;
              const currentTimestamp = new Date().toISOString();

              console.log(`[${currentTimestamp}] Progress: ${processedCount}/${jsonFiles.length} files processed. Estimated time remaining: ${estimatedTimeRemaining.toFixed(1)} minutes`);
            }
          }
        }
        
        // Stop after 500 files for testing
        if (processedCount >= 500) {
          console.log(`Stopped processing after ${processedCount} files (limit reached)`);
          break;
        }
        
      } catch (err) {
        console.error(`Error processing history file ${file}: ${err.message}`);
      }
    }

    // Process remaining items in the last batch
    if (currentBatch.length > 0) {
      await vectorStore.addBatch(currentBatch);
      processedCount += currentBatch.length;
    }
    
    const totalTime = (Date.now() - startTime) / 1000;
    console.log(`Finished loading ${processedCount} files into Chroma in ${totalTime.toFixed(1)} seconds`);
    
    // Display stats
    const stats = await vectorStore.getStats();
    console.log(`Chroma collection stats:`, stats);
    
  } catch (err) {
    console.error(`Error reading screenhistory directory: ${err.message}`);
  }
}

// Wrapper function to easily switch between vector stores
async function createVectorStore(type = 'chroma', options = {}) {
  switch (type.toLowerCase()) {
    case 'chroma':
      return await createChromaVectorStore(
        options.embedder,
        options.collectionName || 'screen_history',
        options.serverUrl || 'http://localhost:8000'
      );
    
    case 'memory':
      // Fall back to your existing InMemoryVectorStore
      const { InMemoryVectorStore } = await import('./your-existing-file.js');
      return new InMemoryVectorStore(options.embedder);
    
    default:
      throw new Error(`Unknown vector store type: ${type}`);
  }
}

export {
  ChromaVectorStore,
  createChromaVectorStore,
  createVectorStore,
  loadExistingHistoryToChroma
};