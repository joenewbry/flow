"""
ChromaDB client for Flow CLI
Handles vector search and data operations
"""

import logging
from typing import Dict, List, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)


class ChromaClientManager:
    def __init__(self, host: str = "localhost", port: int = 8000, persist_path: str = "data/chroma"):
        self.client = None
        self.host = host
        self.port = port
        self.persist_path = persist_path
        self.collections = {}
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
    async def init(self):
        """Initialize ChromaDB client and ensure collections exist."""
        try:
            # Ensure persist directory exists
            from pathlib import Path
            persist_dir = Path(self.persist_path)
            persist_dir.mkdir(parents=True, exist_ok=True)
            
            # Create client with HTTP settings for server connection
            self.client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            # Test connection
            heartbeat = self.client.heartbeat()
            logger.info(f"ChromaDB connected to {self.host}:{self.port}")
            
            # Ensure default collections exist
            await self._ensure_collections()
            
        except Exception as error:
            logger.error(f"Failed to connect to ChromaDB: {error}")
            raise Exception(f"ChromaDB connection failed: {error}")
    
    async def _ensure_collections(self):
        """Ensure required collections exist."""
        default_collections = {
            "screen_history": "Screen tracking history with timestamps and metadata",
            "hourly_summaries": "Hourly activity summaries",
            "daily_summaries": "Daily activity summaries", 
            "monthly_summaries": "Monthly activity summaries",
            "yearly_summaries": "Yearly activity summaries"
        }
        
        try:
            existing_collections = self.client.list_collections()
            existing_names = [c.name for c in existing_collections]
            
            for name, description in default_collections.items():
                if name not in existing_names:
                    collection = self.client.create_collection(
                        name=name,
                        metadata={"description": description},
                        embedding_function=self.embedding_function
                    )
                    logger.info(f"Created collection: {name}")
                else:
                    collection = self.client.get_collection(name)
                    logger.debug(f"Using existing collection: {name}")
                
                self.collections[name] = collection
                
        except Exception as error:
            logger.error(f"Error ensuring collections: {error}")
            raise
    
    def get_collection(self, name: str):
        """Get a specific collection."""
        if name in self.collections:
            return self.collections[name]
        
        try:
            collection = self.client.get_collection(name)
            self.collections[name] = collection
            return collection
        except Exception as error:
            logger.error(f"Error getting collection {name}: {error}")
            raise
    
    async def add_document(self, collection_name: str, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Add a document to a collection."""
        try:
            collection = self.get_collection(collection_name)
            
            collection.add(
                ids=[doc_id],
                documents=[content],
                metadatas=[metadata]
            )
            
            logger.debug(f"Added document {doc_id} to {collection_name}")
            
        except Exception as error:
            logger.error(f"Error adding document to {collection_name}: {error}")
            raise
    
    async def search(self, query: str, collection_name: str = "screen_history", 
                    limit: int = 10, filters: Optional[Dict] = None) -> List[Dict]:
        """Search for documents using vector similarity."""
        try:
            collection = self.get_collection(collection_name)
            
            query_params = {
                "query_texts": [query],
                "n_results": limit
            }
            
            if filters:
                query_params["where"] = filters
            
            results = collection.query(**query_params)
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    result = {
                        "document": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {},
                        "distance": results['distances'][0][i] if results['distances'] and results['distances'][0] else 0,
                        "id": results['ids'][0][i] if results['ids'] and results['ids'][0] else ""
                    }
                    formatted_results.append(result)
            
            return formatted_results
            
        except Exception as error:
            logger.error(f"Error searching collection {collection_name}: {error}")
            return []
    
    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a collection."""
        try:
            collection = self.get_collection(collection_name)
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata if hasattr(collection, 'metadata') else {}
            }
            
        except Exception as error:
            logger.error(f"Error getting stats for {collection_name}: {error}")
            return {"name": collection_name, "count": 0, "metadata": {}}
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [{"name": c.name, "metadata": c.metadata} for c in collections]
        except Exception as error:
            logger.error(f"Error listing collections: {error}")
            return []
    
    async def delete_collection(self, collection_name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(collection_name)
            if collection_name in self.collections:
                del self.collections[collection_name]
            logger.info(f"Deleted collection: {collection_name}")
        except Exception as error:
            logger.error(f"Error deleting collection {collection_name}: {error}")
            raise
    
    def format_search_results(self, results: List[Dict]) -> str:
        """Format search results for display."""
        if not results:
            return "No results found."
        
        output = []
        output.append(f"Found {len(results)} result(s):")
        output.append("─" * 60)
        
        for i, result in enumerate(results, 1):
            metadata = result.get('metadata', {})
            timestamp = metadata.get('timestamp', 'Unknown time')
            app = metadata.get('active_app', 'Unknown app')
            summary = metadata.get('summary', '')
            distance = result.get('distance', 0)
            
            output.append(f"{i}. [{timestamp}] {app}")
            output.append(f"   Summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")
            output.append(f"   Similarity: {1 - distance:.3f}")
            output.append("")
        
        return "\n".join(output)


# Global instance
chroma_client = ChromaClientManager()
