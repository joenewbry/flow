# Memex Multi-Peer Architecture on Prometheus

## Overview

Three laptops (personal, Walmart, Alaska Airlines) each run Memex screen capture locally. OCR data is synced to the Jetson Orin Nano ("Prometheus") via rsync over SSH. Prometheus hosts a single FastAPI server with path-based routing for three MCP endpoints, backed by ChromaDB for vector search and Ollama for AI-powered request validation. Cloudflare Tunnel provides secure public access.

## System Diagram

```
Laptops (Memex capture)          Jetson Orin Nano "Prometheus"
┌─────────────┐                  ┌─────────────────────────────────┐
│ Personal     │──rsync/SSH──┐   │                                 │
│ ~/memex/data │             │   │  Cloudflare Tunnel (cloudflared) │
└─────────────┘             │   │         ▼                        │
┌─────────────┐             ├──▶│  FastAPI :8082                   │
│ Walmart      │──rsync/SSH──┤   │  ├─ Auth (Bearer token)         │
│ ~/memex/data │             │   │  ├─ Rate Limiter                │
└─────────────┘             │   │  ├─ AI Validator (Ollama)        │
┌─────────────┐             │   │  ├─ /personal/mcp               │
│ Alaska       │──rsync/SSH──┘   │  ├─ /walmart/mcp                │
│ ~/memex/data │                 │  └─ /alaska/mcp                 │
└─────────────┘                  │         ▼                        │
                                 │  ChromaDB :8000                  │
                                 │  ├─ personal_ocr_history         │
                                 │  ├─ walmart_ocr_history          │
                                 │  └─ alaska_ocr_history           │
                                 │                                  │
                                 │  Ollama :11434                   │
                                 │  └─ llama3.2:1b                  │
                                 │                                  │
                                 │  /ssd/memex/                     │
                                 │  ├─ data/{personal,walmart,      │
                                 │  │        alaska}/ocr/           │
                                 │  └─ chroma/                      │
                                 └─────────────────────────────────┘
                                          ▼
                                 Claude App / Claude Code
                                 (MCP custom connections)
```

## Data Flow

1. **Capture**: Each laptop runs Memex, taking screenshots every 60s and extracting OCR text into JSON files (~4KB each)
2. **Sync**: Crontab runs `memex-sync.sh` every 5 minutes, rsyncing new OCR files to Prometheus over SSH (key-based auth)
3. **Index**: On Prometheus, `reindex.py` adds new files to the instance-specific ChromaDB collection
4. **Query**: MCP clients connect via Cloudflare Tunnel to `/{instance}/mcp`, authenticated with Bearer tokens
5. **Validate**: For `tools/call` requests, the AI validator checks the request against the security policy
6. **Search**: Tools query either ChromaDB (vector search) or fall back to file-based text search

## API Reference

### Endpoints

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /health` | No | Health check with instance status |
| `GET /` | No | Server info |
| `POST /{instance}/mcp` | Yes | MCP Streamable HTTP transport |
| `GET /{instance}/tools/list` | Yes | Legacy REST tool listing |

### MCP Methods

| Method | Description |
|--------|-------------|
| `initialize` | Create session, returns capabilities |
| `tools/list` | List available tools for the instance |
| `tools/call` | Call a tool (subject to AI validation) |
| `ping` | Keepalive |

### Available Tools (per instance)

| Tool | Description |
|------|-------------|
| `search-screenshots` | Text/vector search with date filters |
| `what-can-i-do` | Capabilities and status |
| `get-stats` | Data statistics |
| `activity-graph` | Activity timeline data |
| `time-range-summary` | Sampled data over time range |
| `sample-time-range` | Flexible windowed sampling |
| `vector-search-windowed` | Semantic search with time windows |
| `search-recent-relevant` | Combined relevance + recency scoring |
| `daily-summary` | Structured daily breakdown |

### Authentication

Each request requires a Bearer token in the Authorization header:
```
Authorization: Bearer <token>
```

- Instance-specific keys (e.g., `PERSONAL_API_KEY`) work for that instance only
- Master key (`MASTER_API_KEY`) works for all instances
- Keys are stored in `/ssd/memex/config/api_keys.env`

## Security Model (4 Layers)

1. **Cloudflare**: DDoS protection, TLS termination, WAF rules
2. **Authentication**: Bearer token per instance + master key
3. **Rate Limiting**: Per-IP (60/min, 500/hr) and per-instance (120/min)
4. **AI Validation**: Ollama llama3.2:1b checks `tools/call` requests against security policy

## Adding a New Instance

1. Create data directory:
   ```bash
   mkdir -p /ssd/memex/data/NEW_INSTANCE/ocr
   ```

2. Add API key to `/ssd/memex/config/api_keys.env`:
   ```
   NEW_INSTANCE_API_KEY=<generated-key>
   ```

3. Update `INSTANCES` in `/ssd/memex/config/prometheus.env`:
   ```
   INSTANCES=personal,walmart,alaska,new_instance
   ```

4. Create sync script on the new laptop (copy `memex-sync.sh`, change `INSTANCE_NAME`)

5. Restart the server:
   ```bash
   sudo systemctl restart memex-server
   ```

6. Run initial sync + reindex:
   ```bash
   # From new laptop:
   ~/bin/memex-sync.sh --reindex
   ```

7. Add Cloudflare DNS route if using subdomain routing

## Configuring Claude App Custom Connections

In Claude App settings, add custom MCP connections:

**Personal:**
- URL: `https://memex.YOUR-DOMAIN.com/personal/mcp`
- Headers: `Authorization: Bearer <PERSONAL_API_KEY>`

**Walmart:**
- URL: `https://memex.YOUR-DOMAIN.com/walmart/mcp`
- Headers: `Authorization: Bearer <WALMART_API_KEY>`

**Alaska:**
- URL: `https://memex.YOUR-DOMAIN.com/alaska/mcp`
- Headers: `Authorization: Bearer <ALASKA_API_KEY>`

## Monitoring & Troubleshooting

### Health Check
```bash
# Manual check
bash /ssd/memex/scripts/health_check.sh

# View logs
tail -f /ssd/memex/logs/prometheus-server.log
tail -f /ssd/memex/logs/audit.log
tail -f /ssd/memex/logs/chromadb.log
```

### Service Management
```bash
# Status
sudo systemctl status memex-chromadb memex-server cloudflared

# Restart
sudo systemctl restart memex-server

# Logs
sudo journalctl -u memex-server -f
```

### Common Issues

| Issue | Fix |
|-------|-----|
| ChromaDB not starting | Check port 8000 is free: `lsof -i :8000` |
| Server 503 | ChromaDB must start before server; check service ordering |
| Auth failures | Verify keys in api_keys.env match client config |
| Rate limited | Check audit.log for client IP; adjust limits in prometheus_server.py |
| AI denying valid requests | Edit security-policy.md and restart server |
| Sync failures | Check SSH key auth: `ssh -i ~/.ssh/id_ed25519 prometheus@prometheus.local` |
| Disk space | Check with `df -h /ssd`; old OCR files can be archived |

## Memory Budget (7.4GB total)

| Component | RAM |
|-----------|-----|
| OS + system | ~1.5GB |
| Ollama + llama3.2:1b | ~1.2GB |
| ChromaDB (3 collections) | ~1.5GB |
| FastAPI server | ~0.3GB |
| Cloudflare Tunnel | ~0.05GB |
| **Headroom** | **~2.85GB** |
