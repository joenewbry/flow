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
    """Tool for searching OCR data."""
    
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
        self.ocr_data_dir = workspace_root / "refinery" / "data" / "ocr"
        
        # Ensure OCR data directory exists
        self.ocr_data_dir.mkdir(parents=True, exist_ok=True)
    
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
    
    async def search_screenshots(
        self,
        query: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Search OCR data from screenshots."""
        try:
            logger.info(f"Searching screenshots: query='{query}', start_date={start_date}, end_date={end_date}, limit={limit}")
            
            # Parse date filters
            start_dt = None
            end_dt = None
            
            if start_date:
                start_dt = datetime.fromisoformat(start_date + "T00:00:00")
            if end_date:
                end_dt = datetime.fromisoformat(end_date + "T23:59:59")
            
            # Get OCR files
            ocr_files = list(self.ocr_data_dir.glob("*.json"))
            ocr_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)  # Most recent first
            
            results = []
            processed = 0
            
            for file_path in ocr_files:
                if len(results) >= limit:
                    break
                
                try:
                    # Check date filter using filename timestamp
                    file_timestamp = self._parse_filename_timestamp(file_path.name)
                    if file_timestamp:
                        if start_dt and file_timestamp < start_dt:
                            continue
                        if end_dt and file_timestamp > end_dt:
                            continue
                    
                    data = self._read_ocr_file(file_path)
                    if not data:
                        continue
                    
                    processed += 1
                    
                    # Simple text search (case-insensitive)
                    text = data.get('text', '').lower()
                    query_lower = query.lower()
                    
                    if query_lower in text:
                        # Calculate relevance score
                        relevance = text.count(query_lower)
                        
                        # Create text preview with context around matches
                        preview = self._create_preview(text, query_lower, max_length=200)
                        
                        results.append({
                            "timestamp": data.get("timestamp"),
                            "screen_name": data.get("screen_name"),
                            "text_length": data.get("text_length", 0),
                            "word_count": data.get("word_count", 0),
                            "text_preview": preview,
                            "relevance": relevance,
                            "match_count": relevance
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
                "date_range": {
                    "start_date": start_date,
                    "end_date": end_date
                },
                "search_summary": {
                    "total_files_available": len(ocr_files),
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
