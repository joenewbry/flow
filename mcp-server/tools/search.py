#!/usr/bin/env python3
"""
Search Tool for Flow MCP Server

Provides search functionality for OCR data from screenshots.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SearchTool:
    """Tool for searching OCR and audio data."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ocr_data_dir = workspace_root / "refinery" / "data" / "ocr"
        self.chroma_client = None
        self.collection = None
        
        # Ensure OCR data directory exists
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Try to initialize ChromaDB client
        self._init_chroma()
    
    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            
            # Try HTTP client first (server running)
            try:
                self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
                self.chroma_client.heartbeat()
                logger.info("Connected to ChromaDB server at localhost:8000")
            except:
                # Fall back to persistent client
                chroma_path = self.workspace_root / "refinery" / "chroma"
                self.chroma_client = chromadb.PersistentClient(path=str(chroma_path))
                logger.info("Connected to ChromaDB using persistent client")
            
            # Try to get the collection
            try:
                self.collection = self.chroma_client.get_collection("screen_ocr_history")
                logger.info("Connected to ChromaDB collection 'screen_ocr_history'")
            except Exception as e:
                logger.warning(f"ChromaDB collection not found: {e}")
                self.collection = None
                
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            self.chroma_client = None
            self.collection = None
    
    def _parse_filename_timestamp(self, filename: str) -> Optional[datetime]:
        """Parse timestamp from OCR filename."""
        try:
            # Format: YYYY-MM-DDTHH-MM-SS-microseconds_ScreenName.json
            if not filename.endswith('.json'):
                return None
            
            timestamp_part = filename.split('_')[0]
            # Convert filename timestamp to datetime
            parts = timestamp_part.split('T')
            if len(parts) != 2:
                return None
            
            date_part = parts[0]  # YYYY-MM-DD
            time_part = parts[1]  # HH-MM-SS-microseconds
            
            # Split time part
            time_components = time_part.split('-')
            if len(time_components) < 3:
                return None
            
            hour, minute = time_components[0], time_components[1]
            
            # Handle seconds and microseconds
            if len(time_components) >= 4:
                second = time_components[2]
                microsecond = time_components[3][:6].ljust(6, '0')
            else:
                second_part = time_components[2]
                if '.' in second_part:
                    second, microsecond = second_part.split('.', 1)
                    microsecond = microsecond[:6].ljust(6, '0')
                else:
                    second = second_part
                    microsecond = '000000'
            
            # Reconstruct ISO format
            iso_string = f"{date_part}T{hour}:{minute}:{second}.{microsecond}"
            return datetime.fromisoformat(iso_string)
            
        except Exception as e:
            logger.debug(f"Error parsing timestamp from filename {filename}: {e}")
            return None
    
    def _read_ocr_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read and parse OCR file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure required fields exist
            if 'timestamp' not in data:
                file_timestamp = self._parse_filename_timestamp(file_path.name)
                if file_timestamp:
                    data['timestamp'] = file_timestamp.isoformat()
                else:
                    data['timestamp'] = datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            
            # Ensure other fields have defaults
            data.setdefault('screen_name', 'unknown')
            data.setdefault('text_length', len(data.get('text', '')))
            data.setdefault('word_count', len(data.get('text', '').split()) if data.get('text') else 0)
            data.setdefault('text', '')
            
            return data
            
        except Exception as e:
            logger.warning(f"Error reading OCR file {file_path}: {e}")
            return None
    
    def _read_audio_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Read and parse audio transcript file (reads markdown for actual transcript text)."""
        try:
            # Read JSON for metadata
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure required fields exist
            data.setdefault('session_id', file_path.stem)
            data.setdefault('start_time', datetime.fromtimestamp(file_path.stat().st_mtime).isoformat())
            
            # Read markdown file for actual transcript text
            md_file = file_path.with_suffix('.md')
            transcript_text = ""
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                    # Extract text from markdown (skip headers and metadata)
                    lines = md_content.split('\n')
                    in_transcript = False
                    for line in lines:
                        if line.startswith('##'):  # Timestamp headers
                            in_transcript = True
                            continue
                        if in_transcript and line.strip() and not line.startswith('#') and not line.startswith('*'):
                            transcript_text += line + " "
            
            # Store transcript text in data for searching
            data['transcript_text'] = transcript_text.strip()
            data.setdefault('transcript', [])
            
            return data
            
        except Exception as e:
            logger.warning(f"Error reading audio file {file_path}: {e}")
            return None
    
    def _parse_audio_filename_timestamp(self, filename: str) -> Optional[datetime]:
        """Parse timestamp from audio filename (format: auto_YYYYMMDD_HHMMSS.json)."""
        try:
            if not filename.endswith('.json'):
                return None
            
            # Remove extension and split
            parts = filename[:-5].split('_')
            if len(parts) < 3 or parts[0] != 'auto':
                return None
            
            date_part = parts[1]  # YYYYMMDD
            time_part = parts[2]  # HHMMSS
            
            # Parse date
            year = date_part[:4]
            month = date_part[4:6]
            day = date_part[6:8]
            
            # Parse time
            hour = time_part[:2]
            minute = time_part[2:4]
            second = time_part[4:6]
            
            # Construct ISO format
            iso_string = f"{year}-{month}-{day}T{hour}:{minute}:{second}"
            return datetime.fromisoformat(iso_string)
            
        except Exception as e:
            logger.debug(f"Error parsing audio timestamp from filename {filename}: {e}")
            return None
    
    async def search_screenshots(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        data_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search OCR and audio data.
        
        Args:
            query: Search query
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            limit: Maximum results to return
            data_type: Filter by type - "ocr", "audio", or None for both
        """
        try:
            logger.info(f"Searching: query='{query}', start_date={start_date}, end_date={end_date}, limit={limit}, data_type={data_type}")
            
            # Use ChromaDB vector search if available
            if self.collection:
                return await self._search_chromadb(query, start_date, end_date, limit, data_type)
            else:
                logger.warning("ChromaDB not available, falling back to file-based search")
                return await self._search_files(query, start_date, end_date, limit, data_type)
            
        except Exception as e:
            logger.error(f"Error searching OCR data: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "total_found": 0
            }
    
    async def _search_chromadb(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        data_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search using ChromaDB vector search."""
        try:
            # Build where filter
            where_filters = []
            
            # Add date filters
            if start_date:
                start_dt = datetime.fromisoformat(start_date + "T00:00:00")
                where_filters.append({"timestamp": {"$gte": start_dt.timestamp()}})
            if end_date:
                end_dt = datetime.fromisoformat(end_date + "T23:59:59")
                where_filters.append({"timestamp": {"$lte": end_dt.timestamp()}})
            
            # Add data_type filter
            if data_type and data_type in ["ocr", "audio"]:
                where_filters.append({"data_type": data_type})
            
            # Build final where clause
            where_clause = None
            if len(where_filters) > 1:
                where_clause = {"$and": where_filters}
            elif len(where_filters) == 1:
                where_clause = where_filters[0]
            
            # Query ChromaDB
            logger.info(f"ChromaDB query with where: {where_clause}")
            query_results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_clause
            )
            
            # Format results
            results = []
            if query_results and query_results["documents"] and query_results["documents"][0]:
                for i in range(len(query_results["documents"][0])):
                    doc = query_results["documents"][0][i]
                    metadata = query_results["metadatas"][0][i] if query_results["metadatas"] else {}
                    distance = query_results["distances"][0][i] if query_results["distances"] else 1.0
                    
                    # Convert distance to relevance (0-1, higher is better)
                    relevance = max(0, 1 - distance)
                    
                    # Extract text preview from document or metadata
                    text_preview = metadata.get("extracted_text", doc)[:200]
                    
                    results.append({
                        "timestamp": metadata.get("timestamp_iso", metadata.get("timestamp", "")),
                        "screen_name": metadata.get("screen_name", "N/A"),
                        "data_type": metadata.get("data_type", "unknown"),  # Include data_type tag
                        "text_length": metadata.get("text_length", 0),
                        "word_count": metadata.get("word_count", 0),
                        "text_preview": text_preview,
                        "relevance": round(relevance, 3),
                        "source": metadata.get("source", "unknown")
                    })
            
            logger.info(f"ChromaDB search completed: {len(results)} results")
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "search_method": "vector_search_chromadb",
                "data_type_filter": data_type or "all",
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
            
        except Exception as e:
            logger.error(f"Error in ChromaDB search: {e}")
            # Fall back to file-based search
            return await self._search_files(query, start_date, end_date, limit, data_type)
    
    async def _search_files(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10,
        data_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback file-based search (supports both OCR and audio files)."""
        try:
            logger.info(f"File-based search (fallback): query='{query}', data_type={data_type}")
            
            # Parse date filters
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date + "T00:00:00")
            if end_date:
                end_dt = datetime.fromisoformat(end_date + "T23:59:59")
            
            # Get files based on data_type filter
            all_files = []
            
            # Get OCR files if requested
            if data_type is None or data_type == "ocr":
                ocr_files = list(self.ocr_data_dir.glob("*.json"))
                all_files.extend([(f, "ocr") for f in ocr_files])
            
            # Get audio files if requested
            if data_type is None or data_type == "audio":
                audio_dir = self.workspace_root / "refinery" / "data" / "audio"
                if audio_dir.exists():
                    audio_files = list(audio_dir.glob("*.json"))
                    all_files.extend([(f, "audio") for f in audio_files])
            
            # Sort by modification time (most recent first)
            all_files.sort(key=lambda x: x[0].stat().st_mtime, reverse=True)
            
            results = []
            processed = 0
            
            for file_path, file_type in all_files:
                if len(results) >= limit:
                    break
                
                try:
                    # Check date filter using filename timestamp
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if not file_timestamp and file_type == "audio":
                        # Try parsing audio filename: auto_YYYYMMDD_HHMMSS.json
                        file_timestamp = self._parse_audio_filename_timestamp(file_path.name)
                    
                    if file_timestamp:
                        if start_dt and file_timestamp < start_dt:
                            continue
                        if end_dt and file_timestamp > end_dt:
                            continue
                    
                    # Read file based on type
                    if file_type == "ocr":
                        data = self._read_ocr_file(file_path)
                        if not data:
                            continue
                        text = data.get('text', '')
                        screen_name = data.get("screen_name", "N/A")
                    else:  # audio
                        data = self._read_audio_file(file_path)
                        if not data:
                            continue
                        # For audio, use transcript text from markdown file
                        text = data.get("transcript_text", "")
                        if not text:
                            # Fallback to transcript array if available
                            text = " ".join([t.get("text", "") for t in data.get("transcript", [])])
                        screen_name = data.get("session_id", "N/A")
                    
                    processed += 1
                    
                    # Simple text search (case-insensitive)
                    text_lower = text.lower()
                    query_lower = query.lower()
                    
                    if query_lower in text_lower:
                        # Calculate relevance score
                        relevance = text_lower.count(query_lower)
                        
                        # Create text preview with context around matches
                        preview = self._create_preview(text_lower, query_lower, max_length=200)
                        
                        results.append({
                            "timestamp": data.get("start_time") if file_type == "audio" else data.get("timestamp"),
                            "screen_name": screen_name,
                            "data_type": file_type,
                            "text_length": len(text),
                            "word_count": len(text.split()),
                            "text_preview": preview,
                            "relevance": relevance,
                            "match_count": relevance,
                            "source": "file_based_search"
                        })
                
                except Exception as e:
                    logger.debug(f"Error searching file {file_path}: {e}")
                    continue
            
            # Sort by relevance (highest first)
            results.sort(key=lambda x: x["relevance"], reverse=True)
            
            logger.info(f"Search completed: {len(results)} results from {processed} files processed")
            
            return {
                "query": query,
                "results": results,
                "total_found": len(results),
                "processed_files": processed,
                "search_method": "file_based_text_search",
                "data_type_filter": data_type or "all",
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "search_summary": {
                    "total_files_available": len(all_files),
                    "files_processed": processed,
                    "matches_found": len(results),
                    "search_terms": [query]
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching OCR data: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": [],
                "total_found": 0
            }
    
    def _create_preview(self, text: str, query: str, max_length: int = 200) -> str:
        """Create a preview of text with context around the search query."""
        try:
            # Find the first occurrence of the query
            index = text.find(query)
            if index == -1:
                # Fallback to beginning of text
                return text[:max_length] + ("..." if len(text) > max_length else "")
            
            # Calculate context window
            context_size = (max_length - len(query)) // 2
            start = max(0, index - context_size)
            end = min(len(text), index + len(query) + context_size)
            
            preview = text[start:end]
            
            # Add ellipsis if truncated
            if start > 0:
                preview = "..." + preview
            if end < len(text):
                preview = preview + "..."
            
            return preview
            
        except Exception as e:
            logger.debug(f"Error creating preview: {e}")
            return text[:max_length] + ("..." if len(text) > max_length else "")
