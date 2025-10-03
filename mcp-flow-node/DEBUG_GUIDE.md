# Flow MCP Server Debugging Guide

When your MCP server is launched by Claude Desktop, here are the best ways to debug and monitor what's happening:

## 🔍 Available Log Files

Claude Desktop automatically captures your MCP server logs in:
- **`~/Library/Logs/Claude/mcp-server-flow.log`** - Your server's stderr output
- **`~/Library/Logs/Claude/mcp.log`** - General MCP connection info
- **`~/Library/Logs/Claude/main.log`** - Claude Desktop main logs

## 🛠️ Quick Debugging Commands

### 1. Real-time Log Monitoring
```bash
# Monitor Flow MCP server logs in real-time with color coding
./debug-logs.sh

# Or use the built-in log viewer
./view-logs.sh
```

### 2. Check Recent Activity
```bash
# Last 20 lines from your server
tail -20 ~/Library/Logs/Claude/mcp-server-flow.log

# Show only errors
./view-logs.sh --errors

# Search for specific terms
./view-logs.sh --search "ChromaDB"
```

### 3. Monitor Connection Issues
```bash
# Check MCP connection status
tail -10 ~/Library/Logs/Claude/mcp.log
```

## 🐛 Common Issues and Solutions

### Issue: Server Not Starting
**Check:** 
```bash
grep -i "error\|failed" ~/Library/Logs/Claude/mcp-server-flow.log | tail -10
```

**Common causes:**
- Missing dependencies (`npm install`)
- Path issues in Claude Desktop config
- Port conflicts (ChromaDB using port 8000)

### Issue: Tools Not Working
**Check:**
```bash
grep "CallToolRequestSchema\|tool" ~/Library/Logs/Claude/mcp-server-flow.log | tail -10
```

**Common causes:**
- Tool parameter validation errors
- ChromaDB connection issues
- File permission problems

### Issue: Silent Failures
**Check:**
```bash
# Look for process exits
grep "exit\|close\|shutdown" ~/Library/Logs/Claude/mcp-server-flow.log | tail -5
```

## 📊 What You Can See in the Logs

From your recent logs, I can see:
1. **Server lifecycle:** Startup, shutdown, process management
2. **Tool calls:** Each time Claude uses your tools
3. **ChromaDB operations:** Database connections and queries
4. **Flow runner output:** Screenshot capture and OCR processing
5. **Error details:** Stack traces and error messages

## 🔧 Enhanced Debugging

### Add Debug Logging
Set environment variable for more verbose output:
```bash
export FLOW_DEBUG=true
```

### Log Analysis Tips
- **Look for patterns:** Repeated errors often indicate config issues
- **Check timestamps:** Correlate errors with your actions in Claude
- **Monitor resource usage:** ChromaDB and Python processes can be resource-intensive

## 🚀 Pro Tips

1. **Keep logs open while testing:** Run `./debug-logs.sh` in a terminal while using Claude
2. **Check after Claude restart:** Fresh logs help isolate new issues
3. **Monitor during tool usage:** Watch logs when running Flow commands
4. **Archive old logs:** Large log files can slow down tail commands

## 📝 Current Status Analysis

From your recent logs, I can see:
- ✅ Server is starting/stopping correctly
- ✅ ChromaDB integration is working
- ✅ Flow runner is capturing screenshots
- ⚠️  Some OCR errors (UTF-8 decoding issues)
- ✅ Tool calls are being processed
- ⚠️  Some search query errors (invalid where clause)

The OCR UTF-8 error suggests some screenshots have binary content that can't be decoded as text, which is normal and can be handled gracefully.
