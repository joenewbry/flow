# Hosting Options

Memex supports three hosting modes. All modes capture screen data locally on your machine; the difference is where ChromaDB and the MCP server run.

## Modes

### 1. Jetson Orin Nano (default)

Capture runs on your laptop. ChromaDB and MCP server run on a Jetson Orin Nano on your local network, optionally exposed via Cloudflare Tunnel.

| Aspect       | Detail                                                    |
|--------------|-----------------------------------------------------------|
| Availability | Always-on (Jetson runs 24/7, low power)                   |
| Security     | Data stays on your LAN unless tunnel is configured        |
| Performance  | GPU-accelerated vector search on Jetson                   |
| Setup        | Requires Jetson with ChromaDB + Prometheus server running |

```
memex config set hosting jetson
```

### 2. Local

Everything runs on your laptop: capture, ChromaDB, MCP server.

| Aspect       | Detail                                        |
|--------------|-----------------------------------------------|
| Availability | Only available when your laptop is on          |
| Security     | Data never leaves your machine                 |
| Performance  | Limited by laptop resources                    |
| Setup        | Simplest — no network configuration needed     |

```
memex config set hosting local
```

### 3. Remote Self-Host

Capture runs on your laptop. ChromaDB and MCP server run on a remote VPS or server, accessed via SSH or tunnel.

| Aspect       | Detail                                              |
|--------------|-----------------------------------------------------|
| Availability | Depends on VPS uptime (typically high)               |
| Security     | Data transits your network to the remote server      |
| Performance  | Depends on server specs and network latency          |
| Setup        | Requires SSH access and services running on remote   |

```
memex config set hosting remote
```

## Switching Modes

```bash
# Switch to local
memex config set hosting local

# Switch to Jetson
memex config set hosting jetson

# Switch to remote
memex config set hosting remote

# Verify
memex config

# Restart to apply
memex start
```

## Instance Configuration

Instance config is stored at `~/.memex/instance.json` (permissions `0600`).

| Field                | Description                                  | Default       |
|----------------------|----------------------------------------------|---------------|
| `hosting_mode`       | `local`, `jetson`, or `remote`               | `jetson`      |
| `instance_name`      | Name for this instance                       | `personal`    |
| `jetson_host`        | Jetson IP or hostname                        | —             |
| `jetson_chroma_port` | ChromaDB port on Jetson                      | `8000`        |
| `jetson_mcp_port`    | MCP port on Jetson                           | `8082`        |
| `jetson_tunnel_url`  | Cloudflare Tunnel URL (optional)             | —             |
| `remote_host`        | Remote server IP or hostname                 | —             |
| `remote_ssh_port`    | SSH port on remote server                    | `22`          |
| `remote_chroma_port` | ChromaDB port on remote server               | `8000`        |
| `remote_mcp_port`    | MCP port on remote server                    | `8082`        |
| `remote_tunnel_url`  | Tunnel URL for remote (optional)             | —             |

## First-Run Setup

Running `memex start` on a fresh install triggers an interactive setup:

1. Choose hosting mode (default: Jetson)
2. Set instance name (default: personal)
3. Configure mode-specific connection details
4. Instance config saved to `~/.memex/instance.json`

## Usage Tracking

Every MCP tool call is logged to `~/.memex/usage.jsonl` (append-only). This tracks:
- Timestamp, tool name, query length, result count, duration
- Data sync events (files synced, bytes stored)

View today's usage in `memex status`. This data is the foundation for future pricing models but no billing logic exists yet.

## Future: Pricing Models

Two models are planned (not yet implemented):

1. **Subscription** — Monthly plan with usage limits (tool calls/month, storage cap)
2. **Usage-based API keys** — Pay per tool call and per GB stored

Usage tracking from day one ensures accurate metering when pricing is introduced.
