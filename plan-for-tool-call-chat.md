# Plan for Tool Call Chat Implementation

## Overview
Implement a chat interface in the Flow dashboard that enables tool calling via OpenAI's API. The chat will communicate with the MCP server via WebSocket, support asynchronous tool execution, and include a message queue system similar to Cursor's interface.

## Requirements
- [ ] Use OPENAI_API_KEY from .env file
- [ ] WebSocket-based communication between dashboard and MCP server
- [ ] Visual indication when tools are being called
- [ ] Message queue that processes messages one at a time
- [ ] Allow users to type multiple messages in a row
- [ ] Support all existing MCP tools through the chat interface

## Architecture

### Components
1. **Frontend (Dashboard Chat Tab)**
   - Message display area with tool call indicators
   - Input area with queue visualization
   - Tool execution status indicators
   - Message queue UI showing pending messages

2. **Backend (Dashboard API)**
   - WebSocket endpoint for chat messages
   - OpenAI API integration
   - Message queue manager
   - Tool call coordinator

3. **Integration Layer**
   - Bridge between OpenAI tool calls and MCP server tools
   - Tool definition mapper
   - Response formatter

## Implementation Steps

### Phase 1: Environment and Configuration Setup
- [x] Verify .env file structure for OPENAI_API_KEY
- [x] Create .env.example file if needed
- [x] Add OpenAI SDK to dashboard requirements.txt
- [x] Create configuration module for API key loading
- [x] Add error handling for missing API key

### Phase 2: Backend API Development
- [x] Create `/api/chat/send` endpoint for chat messages
- [x] Create `/ws/chat` WebSocket endpoint for real-time communication (using existing WebSocket)
- [x] Implement message queue manager class
  - [x] Queue data structure for pending messages
  - [x] Processing state management
  - [x] Message priority handling
- [x] Implement OpenAI integration module
  - [x] Load API key from .env
  - [x] Define tool schemas matching MCP tools
  - [x] Handle streaming responses
  - [x] Parse tool calls from OpenAI responses
- [x] Create tool call coordinator
  - [x] Map OpenAI tool calls to MCP tools
  - [x] Execute tools via MCP server
  - [x] Handle tool responses
  - [x] Format results for chat display

### Phase 3: MCP Tools Integration
- [x] Create tool definitions for OpenAI
  - [x] search-screenshots
  - [x] get-stats
  - [x] activity-graph
  - [x] time-range-summary
  - [x] start-flow
  - [x] stop-flow
  - [x] what-can-i-do
  - [ ] create-webpage (not included in initial release)
  - [ ] list-webpages (not included in initial release)
  - [ ] delete-webpage (not included in initial release)
  - [ ] get-webpage-url (not included in initial release)
- [x] Implement tool call executor
  - [x] Direct calls to MCP tool classes
  - [x] Error handling for tool failures
  - [x] Retry logic for network issues
- [x] Create response formatter
  - [x] Format JSON responses for chat display
  - [x] Handle different result types
  - [x] Create readable summaries

### Phase 4: Frontend Chat Interface
- [x] Update dashboard.html Chat page
  - [x] Enhanced message display area
  - [x] Tool execution indicator UI
  - [x] Message queue visualization
  - [x] Input area with send button
- [x] Update dashboard.css
  - [x] Chat message styles (user, assistant, system, tool)
  - [x] Tool call indicator animations
  - [x] Queue item styles
  - [x] Loading states
- [x] Update dashboard.js
  - [x] WebSocket connection management (using existing)
  - [x] Message sending function
  - [x] Message queue UI updates
  - [x] Display incoming messages
  - [x] Show tool execution status
  - [x] Handle Enter key to send
  - [x] Allow Shift+Enter for new lines

### Phase 5: Message Queue System
- [x] Implement queue manager
  - [x] Add message to queue
  - [x] Process next message when ready
  - [x] Track processing state
  - [x] Handle queue cancellation
- [x] Update UI for queue
  - [x] Show queued messages
  - [x] Show currently processing message
  - [ ] Allow removing queued messages (future enhancement)
  - [x] Show position in queue
- [x] Add queue controls
  - [x] Clear queue button
  - [ ] Pause/resume processing (future enhancement)
  - [ ] Cancel current processing (future enhancement)

### Phase 6: Tool Call Visualization
- [x] Design tool call indicators
  - [x] Show when tool is being called
  - [x] Display tool name and parameters
  - [x] Show execution progress
  - [x] Display results
- [x] Implement status messages
  - [x] "Executing tool: X..."
  - [x] "Tool X completed"
  - [x] Error messages
- [x] Add animations
  - [x] Basic message display
  - [ ] Spinner for processing (future enhancement)
  - [ ] Slide-in for new messages (future enhancement)
  - [ ] Highlight for tool results (future enhancement)

### Phase 7: Error Handling and Edge Cases
- [ ] Handle API key errors
  - [ ] Clear error message if key missing
  - [ ] Instructions for adding key
- [ ] Handle OpenAI API errors
  - [ ] Rate limiting
  - [ ] Invalid requests
  - [ ] Network errors
- [ ] Handle MCP tool errors
  - [ ] Tool not available
  - [ ] Invalid parameters
  - [ ] Execution failures
- [ ] Handle WebSocket errors
  - [ ] Connection lost
  - [ ] Reconnection logic
  - [ ] Message recovery

### Phase 8: Testing and Refinement
- [ ] Test basic chat functionality
  - [ ] Send simple messages
  - [ ] Receive responses
  - [ ] Multiple messages in sequence
- [ ] Test tool calling
  - [ ] Each individual tool
  - [ ] Multiple tools in one conversation
  - [ ] Complex tool parameters
- [ ] Test queue system
  - [ ] Multiple queued messages
  - [ ] Queue while processing
  - [ ] Cancel and clear
- [ ] Test error scenarios
  - [ ] Missing API key
  - [ ] Invalid tool calls
  - [ ] Network issues
- [ ] Performance testing
  - [ ] Multiple concurrent users (if applicable)
  - [ ] Large responses
  - [ ] Queue backlog

### Phase 9: Documentation and Polish
- [ ] Add inline code documentation
- [ ] Create user guide for chat feature
- [ ] Add tooltips and help text
- [ ] Update README with chat instructions
- [ ] Add example conversations

### Phase 10: Integration and Deployment
- [ ] Ensure compatibility with existing dashboard features
- [ ] Test on clean environment
- [ ] Create migration notes if needed
- [ ] Update deployment documentation
- [ ] Merge to main branch

## Technical Details

### OpenAI Tool Definitions Format
```json
{
  "name": "search_screenshots",
  "description": "Search through OCR data from screenshots",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query for the OCR text content"
      },
      "start_date": {
        "type": "string",
        "description": "Start date for search (YYYY-MM-DD format, optional)"
      }
    },
    "required": ["query"]
  }
}
```

### Message Queue Data Structure
```python
class MessageQueue:
    def __init__(self):
        self.queue = []  # List of pending messages
        self.processing = False
        self.current_message = None
```

### WebSocket Message Format
```json
{
  "type": "chat_message|tool_call|tool_result|queue_update|error",
  "data": {
    "message": "...",
    "tool_name": "...",
    "tool_params": {...},
    "result": {...},
    "queue_position": 0
  },
  "timestamp": "2025-10-14T..."
}
```

## Files to Create/Modify

### New Files
- `dashboard/lib/chat_manager.py` - Chat and queue management
- `dashboard/lib/openai_client.py` - OpenAI API integration
- `dashboard/lib/tool_executor.py` - Tool execution coordination
- `dashboard/api/chat.py` - Chat API endpoints

### Modified Files
- `dashboard/app.py` - Add chat endpoints and WebSocket
- `dashboard/templates/dashboard.html` - Update Chat tab UI
- `dashboard/static/js/dashboard.js` - Add chat functionality
- `dashboard/static/css/dashboard.css` - Add chat styles
- `dashboard/requirements.txt` - Add openai package
- `.env.example` - Add OPENAI_API_KEY

## Dependencies to Add
```
openai>=1.0.0
python-dotenv>=1.0.0  # Already included
httpx>=0.25.0  # Already included for MCP calls
```

## Success Criteria
- ✅ Users can send chat messages and receive AI responses
- ✅ AI can call all MCP tools through the chat interface
- ✅ Users see clear indicators when tools are being executed
- ✅ Message queue displays pending messages
- ✅ Users can queue multiple messages that process sequentially
- ✅ Errors are handled gracefully with helpful messages
- ✅ Chat works reliably with the existing dashboard features

## Notes
- Consider rate limiting on the frontend to prevent API abuse
- Add cost monitoring if needed (OpenAI API costs)
- Store chat history in local storage for persistence across page reloads
- Consider adding chat export functionality
- May want to add conversation context management (clear context, etc.)

