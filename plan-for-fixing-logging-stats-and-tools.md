# Plan for Fixing Logging, Statistics, and MCP Tools

## Overview
This plan addresses multiple related issues:
1. Logging systems showing as "not available"
2. Time statistics showing incorrect data (user has used up to 3 screens)
3. Verifying and fixing MCP tools including search range tool
4. Creating new MCP tools for flexible time range sampling
5. Adding vector search with windowing
6. Implementing recency + relevance search tool

## Task 2: Fix Logging Systems

### Diagnosis
- [x] Check which logging systems are showing as not available
- [x] Investigate log file paths and permissions
- [x] Check if WebSocket log broadcasting is working
- [x] Verify log handler initialization
- [x] Test each subsystem's logging separately

### Issue Identification
- [x] Screen Capture logging
- [x] ChromaDB logging  
- [x] Dashboard logging
- [x] MCP Server logging

### Implementation
- [x] Fix log file paths if incorrect
- [x] Update process manager to properly track log files
- [x] Implement log file reading endpoints if missing
- [x] Update WebSocket log broadcasting
- [x] Add fallback for missing log files
- [x] Create log directories if they don't exist

### Testing
- [x] Verify logs appear in dashboard
- [x] Test WebSocket real-time log updates
- [x] Check all four subsystems
- [x] Verify log level filtering works

## Task 3: Fix Time Statistics

### Diagnosis
- [x] Check what statistics are being displayed
- [ ] Investigate how screen detection works
- [ ] Review OCR file naming and metadata
- [ ] Check screen name extraction logic
- [ ] Analyze activity timeline data

### Issue Identification
- [ ] How many screens are actually in use?
- [ ] Are OCR files properly labeled with screen info?
- [ ] Is screen count calculation correct?
- [ ] Are files from different screens being counted?

### Implementation
- [ ] Fix screen name extraction from OCR files
- [ ] Update unique screen calculation logic
- [ ] Add proper screen detection and tracking
- [ ] Update statistics aggregation
- [ ] Fix activity timeline screen counting

### Testing
- [ ] Verify screen count matches reality
- [ ] Test with multiple monitors
- [ ] Check historical data accuracy
- [ ] Validate statistics calculations

## Task 4: Verify and Fix MCP Tools

### Tools to Verify
- [x] search-screenshots - basic text search
- [x] get-stats - system statistics
- [x] activity-graph - timeline generation
- [x] time-range-summary - existing range tool
- [ ] Investigate "search range tool" mentioned in requirements

### Diagnosis
- [ ] Test each tool through MCP interface
- [ ] Check tool parameters and responses
- [ ] Verify error handling
- [ ] Test edge cases

### Fixes Needed
- [ ] Fix any broken tools
- [ ] Update tool schemas if incorrect
- [ ] Add missing error handling
- [ ] Improve response formatting

### Testing
- [ ] Test each tool with various inputs
- [ ] Verify responses are correct
- [ ] Test error conditions
- [ ] Validate with Claude Desktop

## Task 5: Flexible Time Range Sampling Tool

### Requirements
- Sample data over a time range with flexible windows
- Data is sparse - pick first element in each window
- Tool should answer: "What did I work on between 9am-5pm yesterday/last week?"
- Smart window sizing based on overall range

### Design
- [ ] Design window calculation algorithm
  - [ ] Calculate total time range
  - [ ] Determine optimal window size
  - [ ] Ensure windows don't create too much/too little data
- [ ] Implement sparse data strategy
  - [ ] Find first valid OCR entry in each window
  - [ ] Handle empty windows gracefully
  - [ ] Return meaningful summary

### Tool Specification
```
Name: sample_time_range
Description: Sample OCR data over a time range with intelligent windowing
Parameters:
  - start_time: ISO datetime or relative (e.g., "yesterday 9am")
  - end_time: ISO datetime or relative (e.g., "yesterday 5pm") 
  - max_samples: Maximum number of samples to return (default: 24)
  - min_window_minutes: Minimum window size (default: 15)
  - include_text: Include OCR text in results (default: true)
```

### Implementation
- [ ] Create new tool file: `mcp-server/tools/sampling.py`
- [ ] Implement SamplingTool class
- [ ] Add time parsing (relative and absolute)
- [ ] Implement window calculation logic
- [ ] Add sparse data sampling strategy
- [ ] Format results for readability
- [ ] Register tool in MCP server
- [ ] Add to OpenAI tool definitions

### Testing
- [ ] Test with various time ranges
- [ ] Test relative time parsing
- [ ] Verify window sizing
- [ ] Check sparse data handling
- [ ] Validate result quality

## Task 6: Vector Search with Windowing

### Requirements
- Use windowing approach with vector search
- Pick first vector match for each window OR NONE
- Adjust window size based on overall range
- Handle context window limitations

### Design
- [ ] Integrate with ChromaDB for vector search
- [ ] Design window + vector search algorithm
  - [ ] Split time range into windows
  - [ ] Perform vector search within each window
  - [ ] Return top match per window or None
  - [ ] Smart window sizing
- [ ] Handle result aggregation and ranking

### Tool Specification
```
Name: vector_search_windowed
Description: Vector search across time with intelligent windowing
Parameters:
  - query: Search query (semantic)
  - start_time: Start of time range
  - end_time: End of time range
  - max_results: Maximum windows to return (default: 20)
  - min_relevance: Minimum relevance score (default: 0.5)
```

### Implementation  
- [ ] Create new tool file: `mcp-server/tools/vector_search.py`
- [ ] Import ChromaDB client
- [ ] Implement VectorSearchTool class
- [ ] Add windowing logic
- [ ] Perform vector search per window
- [ ] Aggregate and rank results
- [ ] Format for display
- [ ] Register tool in MCP server
- [ ] Add to OpenAI tool definitions

### Testing
- [ ] Test semantic search quality
- [ ] Verify window distribution
- [ ] Check relevance filtering
- [ ] Test with various queries
- [ ] Validate across different time ranges

## Task 7: Recency + Relevance Search

### Requirements
- Find most recent and relevant information
- As OCR screenshots are collected, recent = current status vs past
- Answer: "What's the current status of project XYZ?"
- Need both vector search AND recency
- Check if ChromaDB supports this natively
- Implement expanding windows if first search doesn't succeed

### Research
- [ ] Check ChromaDB documentation for recency+relevance
- [ ] Research scoring algorithms combining recency and relevance
- [ ] Design fallback strategy with expanding windows

### Design
- [ ] Design combined scoring formula
  - [ ] Vector similarity score (0-1)
  - [ ] Recency score (0-1) based on timestamp
  - [ ] Weighted combination
- [ ] Implement expanding window strategy
  - [ ] Start with recent window (e.g., last 7 days)
  - [ ] Expand if no good matches
  - [ ] Stop at configurable max range

### Tool Specification
```
Name: search_recent_relevant
Description: Find most recent and relevant information
Parameters:
  - query: Search query (semantic)
  - max_results: Maximum results (default: 10)
  - initial_days: Initial search window in days (default: 7)
  - max_days: Maximum search window if expanding (default: 90)
  - recency_weight: Weight for recency vs relevance (default: 0.5)
  - min_score: Minimum combined score (default: 0.6)
```

### Implementation
- [ ] Create new tool file: `mcp-server/tools/recent_search.py`
- [ ] Implement RecentSearchTool class
- [ ] Add scoring algorithm
- [ ] Implement expanding window search
- [ ] Add result ranking and formatting
- [ ] Register tool in MCP server
- [ ] Add to OpenAI tool definitions

### Testing
- [ ] Test recency scoring
- [ ] Verify relevance ranking
- [ ] Test expanding windows
- [ ] Validate combined scores
- [ ] Test with real-world queries

## Task 8: New Tool Ideas Research

### Approach
- [ ] Analyze available data types
  - [ ] OCR screenshots
  - [ ] Timestamps and metadata
  - [ ] Screen information
  - [ ] Activity patterns
  - [ ] (Future) Audio transcripts
- [ ] Research common work scenarios
- [ ] Identify pain points and useful queries

### Tool Ideas to Explore
- [ ] Daily/weekly summary generator
- [ ] Meeting notes extractor
- [ ] Code snippet finder
- [ ] Documentation searcher
- [ ] Communication thread follower
- [ ] Focus time analyzer
- [ ] Context switcher
- [ ] Project timeline builder

### Deliverable
- [ ] Create new-tool-options.md
- [ ] Document each tool idea
- [ ] Include use cases
- [ ] Add example queries
- [ ] Create mermaid diagrams
- [ ] Prioritize by usefulness

## Success Criteria

### Logging (Task 2)
- ✅ All four logging systems show as "available"
- ✅ Logs display in real-time in dashboard
- ✅ Log filtering works correctly
- ✅ WebSocket broadcasting functions properly

### Statistics (Task 3)  
- ✅ Screen count accurately reflects reality (3 screens)
- ✅ Time statistics are correct
- ✅ Activity timeline shows accurate data
- ✅ All-time stats are properly calculated

### MCP Tools (Task 4)
- ✅ All existing tools work correctly
- ✅ Search range tool identified and working
- ✅ Tools can be called from Claude Desktop
- ✅ Error handling is robust

### New Tools (Tasks 5-7)
- ✅ Three new tools implemented and working
- ✅ Tools integrated with OpenAI chat
- ✅ Tools accessible via Claude Desktop
- ✅ Documentation complete
- ✅ Tests passing

### Research (Task 8)
- ✅ Comprehensive tool ideas document created
- ✅ Use cases clearly defined
- ✅ Prioritization complete
- ✅ Ready for future implementation

## Files to Create/Modify

### New Files
- `mcp-server/tools/sampling.py` - Flexible time range sampling
- `mcp-server/tools/vector_search.py` - Vector search with windowing
- `mcp-server/tools/recent_search.py` - Recency + relevance search
- `new-tool-options.md` - Tool ideas and research
- `logs/README.md` - Logging system documentation

### Modified Files
- `dashboard/lib/process_manager.py` - Fix logging tracking
- `dashboard/lib/data_handler.py` - Fix statistics calculation
- `refinery/lib/screen_detection.py` - Fix screen counting
- `mcp-server/server.py` - Register new tools
- `dashboard/lib/openai_client.py` - Add new tool definitions
- `mcp-server/tools/search.py` - Potential fixes
- `mcp-server/tools/activity.py` - Potential fixes

