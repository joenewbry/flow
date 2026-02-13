# Memex — Current Architecture

## System Overview

```mermaid
graph TB
    subgraph Laptop ["Your Laptop (macOS)"]
        CLI["CLI (typer)"]
        Refinery["Refinery<br/>Screen Capture + OCR"]
        Recorder["Recorder<br/>Swift Audio Capture"]
        MCP_Local["MCP HTTP Server<br/>:8082"]
        Desktop["Desktop App<br/>Electron + React"]
        ChromaDB_Local["ChromaDB<br/>:8000"]
    end

    subgraph Jetson ["Jetson Orin Nano (default host)"]
        Prometheus["Prometheus Server<br/>FastAPI :8082"]
        ChromaDB_Jetson["ChromaDB<br/>:8000"]
        Ollama["Ollama<br/>llama3.2:1b"]
        CF["Cloudflare Tunnel"]
    end

    subgraph External ["External Services"]
        Claude["Anthropic Claude API"]
        OpenAI["OpenAI API"]
        Grok["Grok API"]
        Claude_Desktop["Claude Desktop"]
    end

    CLI --> MCP_Local
    CLI --> ChromaDB_Local
    CLI --> Claude & OpenAI & Grok
    Refinery -->|OCR JSON| ChromaDB_Local
    Refinery -->|rsync/SSH| ChromaDB_Jetson
    Recorder -->|.m4a files| Refinery
    Desktop -->|HTTP :8082| MCP_Local
    MCP_Local --> ChromaDB_Local
    Claude_Desktop -->|stdio or HTTP| MCP_Local
    Claude_Desktop -->|HTTP via tunnel| Prometheus
    Prometheus --> ChromaDB_Jetson
    Prometheus --> Ollama
    CF --> Prometheus
```

## Data Pipeline

```mermaid
flowchart LR
    A["Screen Capture<br/>every 60s"] --> B["Tesseract OCR<br/>4 threads"]
    B --> C["JSON Files<br/>refinery/data/ocr/"]
    C --> D["ChromaDB<br/>Vector Embeddings"]

    E["Audio Capture<br/>ScreenCaptureKit +<br/>AVAudioEngine"] --> F[".m4a Files<br/>refinery/data/audio/<br/>rotate every 5min"]

    D --> G["MCP Tools<br/>search, stats,<br/>daily-summary"]
    G --> H["Claude / Cursor<br/>AI Assistants"]
    G --> I["CLI Commands<br/>ask, chat, search"]
    G --> J["Desktop App<br/>Stats + Activity"]
```

## Hosting Modes

```mermaid
flowchart TB
    subgraph Local ["Local Mode"]
        direction TB
        L_Cap["Capture + OCR"] --> L_Chroma["ChromaDB :8000<br/>localhost"]
        L_MCP["MCP Server :8082<br/>localhost"] --> L_Chroma
    end

    subgraph Jetson_Mode ["Jetson Mode (default)"]
        direction TB
        J_Cap["Capture + OCR<br/>(laptop)"] -->|rsync / SSH| J_Chroma["ChromaDB :8000<br/>192.168.x.x (Jetson)"]
        J_Prom["Prometheus :8082<br/>(Jetson)"] --> J_Chroma
        J_CF["Cloudflare Tunnel"] --> J_Prom
    end

    subgraph Remote ["Remote Mode"]
        direction TB
        R_Cap["Capture + OCR<br/>(laptop)"] -->|SSH tunnel| R_Chroma["ChromaDB :8000<br/>VPS / remote"]
        R_MCP["MCP Server :8082<br/>(remote)"] --> R_Chroma
    end
```

## CLI Command Map

```mermaid
graph LR
    memex["memex"]

    memex --> start["start<br/>First-run setup +<br/>mode-specific startup"]
    memex --> stop["stop"]
    memex --> status["status<br/>Health + hosting mode +<br/>usage counts"]
    memex --> doctor["doctor<br/>Full diagnostics"]

    memex --> chat["chat<br/>Interactive AI chat"]
    memex --> ask["ask<br/>AI search (streaming)"]
    memex --> search["search<br/>Direct text search"]
    memex --> standup["standup<br/>Daily summary"]

    memex --> stats["stats<br/>Activity statistics"]
    memex --> graph["graph<br/>Usage graph"]
    memex --> watch["watch<br/>Live capture view"]
    memex --> sync["sync<br/>Files → ChromaDB"]

    memex --> config["config<br/>set, path"]
    memex --> auth["auth<br/>login, logout, status"]
    memex --> record["record<br/>start, stop, status"]
    memex --> automate["automate<br/>Run markdown automations"]
    memex --> logs["logs"]
```

## Service Layer

```mermaid
classDiagram
    class CaptureService {
        start(foreground)
        stop()
        is_running() → bool, pid
    }

    class AudioService {
        start(output_dir, format)
        stop()
        is_running() → bool, pid
        get_recording_count() → int
        get_total_size() → int
    }

    class DatabaseService {
        search(query, start_date, end_date)
        get_capture_count(start, end)
        get_stats()
    }

    class HealthService {
        check_chroma_server()
        check_mcp_server()
        check_capture_process()
        check_ssh_connection(host, port)
        check_remote_url(url)
        get_storage_size()
        get_today_capture_count()
    }

    class AIService {
        chat(messages, stream)
        search_screenshots(query)
        get_activity_stats()
    }

    class MCPService {
        start()
        stop()
        is_running() → bool, pid
    }

    class InstanceService {
        exists() → bool
        load() → InstanceConfig
        save(config)
        set_hosting_mode(mode)
    }

    class UsageTracker {
        log_tool_call(tool, instance, ...)
        log_data_sync(instance, files, bytes)
        get_usage_summary(period)
        get_storage_by_instance()
    }

    DatabaseService --> HealthService : uses ChromaDB checks
    AIService --> DatabaseService : tool execution
    InstanceService --> HealthService : remote checks
```

## MCP Tool Architecture

```mermaid
flowchart TB
    subgraph Transport ["Transport Layer"]
        STDIO["stdio<br/>(Claude Desktop)"]
        HTTP["HTTP :8082<br/>(Cursor, Desktop App)"]
        SSE["SSE legacy<br/>(older Cursor)"]
    end

    subgraph Server ["FlowMCPServer"]
        Router["Tool Router"]
    end

    subgraph Tools ["Tools (mcp-server/tools/)"]
        T1["search-screenshots<br/>Text + vector search"]
        T2["get-stats<br/>Data statistics"]
        T3["activity-graph<br/>Hourly/daily timeline"]
        T4["time-range-summary<br/>Sampled summaries"]
        T5["daily-summary<br/>Structured day breakdown"]
        T6["what-can-i-do<br/>Capabilities"]
        T7["start-flow / stop-flow<br/>Process control"]
    end

    subgraph Tracking ["Usage Tracking"]
        JSONL["~/.memex/usage.jsonl<br/>Append-only log"]
    end

    STDIO --> Router
    HTTP --> Router
    SSE --> Router
    Router --> T1 & T2 & T3 & T4 & T5 & T6 & T7
    Router -->|after each call| JSONL
    T1 & T2 & T3 & T4 & T5 --> ChromaDB["ChromaDB"]
```

## Prometheus Multi-Instance Server (Jetson)

```mermaid
flowchart TB
    Client["Client Request<br/>/{instance}/mcp"]

    Client --> CORS["CORS Middleware"]
    CORS --> Size["Size Limit Check<br/>1MB max"]
    Size --> Auth["Auth<br/>Bearer Token<br/>per-instance keys"]
    Auth --> Rate["Rate Limiter<br/>60/min IP, 120/min instance"]
    Rate --> AI["AI Validator<br/>Ollama llama3.2:1b"]
    AI --> Route{"Instance Router"}

    Route -->|/personal/mcp| P["Personal Instance<br/>personal_ocr_history"]
    Route -->|/walmart/mcp| W["Walmart Instance<br/>walmart_ocr_history"]
    Route -->|/alaska/mcp| A["Alaska Instance<br/>alaska_ocr_history"]

    P & W & A --> Chroma["ChromaDB :8000"]

    subgraph Logging
        Audit["audit.log"]
        Usage["usage.jsonl"]
    end

    Route --> Audit
    Route --> Usage
```

## Configuration & State

```mermaid
flowchart TB
    subgraph Config ["~/.memex/"]
        instance["instance.json<br/>hosting_mode, hosts,<br/>ports, tunnel URLs"]
        creds["credentials.json<br/>API keys (Anthropic,<br/>OpenAI, Grok)"]
        usage["usage.jsonl<br/>Tool call + sync events"]
    end

    subgraph Settings ["Settings Singleton"]
        S["Settings.__post_init__<br/>1. Load defaults<br/>2. Read instance.json<br/>3. Override chroma_host,<br/>   chroma_port, mcp_http_port"]
    end

    subgraph EnvVars ["Environment Variables"]
        E1["ANTHROPIC_API_KEY"]
        E2["OPENAI_API_KEY"]
        E3["XAI_API_KEY"]
    end

    instance --> S
    S --> |"All commands auto-route<br/>to correct server"| Commands["search, sync, stats,<br/>ask, chat, status"]
    creds --> AI_Service["AIService"]
    E1 & E2 & E3 -->|"priority over<br/>credentials.json"| AI_Service
    usage --> Status["memex status<br/>usage counts"]
```

## File System Layout

```
flow/
├── cli/                          # CLI application
│   ├── main.py                   # Typer app, all command registration
│   ├── __init__.py               # __version__
│   ├── config/
│   │   ├── settings.py           # Settings dataclass + instance override
│   │   └── credentials.py        # API key storage (~/.memex/credentials.json)
│   ├── commands/
│   │   ├── start.py              # First-run setup + mode dispatch
│   │   ├── stop.py               # Stop daemon
│   │   ├── status.py             # Health + hosting mode + usage
│   │   ├── config.py             # Config view/set (hosting mode switch)
│   │   ├── doctor.py             # Full diagnostics
│   │   ├── search.py             # Direct text search
│   │   ├── ask.py                # AI-powered search (streaming)
│   │   ├── chat.py               # Interactive AI chat
│   │   ├── stats.py              # Activity statistics
│   │   ├── graph.py              # Usage graph
│   │   ├── sync.py               # Files → ChromaDB
│   │   ├── watch.py              # Live capture view
│   │   ├── standup.py            # Daily standup summary
│   │   ├── auth.py               # API key management
│   │   ├── record.py             # Audio recording control
│   │   ├── automate.py           # Markdown automations
│   │   ├── logs.py               # Service log viewer
│   │   ├── contact.py            # Contact info
│   │   └── help_cmd.py           # Extended help
│   ├── services/
│   │   ├── capture.py            # Screen capture process management
│   │   ├── database.py           # ChromaDB search + file-based fallback
│   │   ├── health.py             # Dependency/service/permission checks
│   │   ├── ai.py                 # Multi-provider AI (Claude, GPT, Grok)
│   │   ├── mcp.py                # MCP server process management
│   │   ├── audio.py              # Audio recording management
│   │   ├── chroma.py             # ChromaDB command detection
│   │   ├── instance.py           # Hosting mode config (local/jetson/remote)
│   │   └── usage.py              # Usage tracking (JSONL metering)
│   └── display/
│       ├── components.py         # Rich UI components
│       └── colors.py             # Color palette
│
├── refinery/                     # Capture + OCR pipeline
│   ├── run.py                    # FlowRunner — main capture loop
│   ├── lib/
│   │   ├── screen_detection.py   # Multi-display detection (Quartz)
│   │   └── chroma_client.py      # ChromaDB client wrapper
│   └── data/
│       ├── ocr/                  # {timestamp}_{screen}.json files
│       └── audio/                # {timestamp}_{type}.m4a files
│
├── mcp-server/                   # MCP server (local)
│   ├── server.py                 # FlowMCPServer (stdio transport)
│   ├── http_server.py            # HTTP transport (FastAPI :8082)
│   └── tools/
│       ├── search.py             # search-screenshots
│       ├── stats.py              # get-stats
│       ├── activity.py           # activity-graph, time-range-summary
│       ├── daily_summary.py      # daily-summary
│       ├── system.py             # what-can-i-do, start/stop-flow
│       ├── sampling.py           # Time window sampling
│       ├── vector_search.py      # Semantic vector search
│       └── recent_search.py      # Relevance + recency scoring
│
├── prometheus/                   # Multi-instance server (Jetson)
│   └── server/
│       ├── prometheus_server.py  # FastAPI, path-based routing
│       ├── instance_manager.py   # MemexInstance management
│       ├── auth.py               # Bearer token auth
│       ├── rate_limiter.py       # Per-IP/instance rate limiting
│       └── ai_validator.py       # Ollama-based request validation
│
├── desktop/                      # Desktop dashboard
│   ├── electron/
│   │   ├── main.ts               # Electron main process
│   │   ├── preload.js            # Context bridge
│   │   └── tray.ts               # System tray
│   └── src/
│       ├── App.tsx               # React router
│       ├── pages/                # Stats, Activity, Chat
│       ├── components/           # Sidebar, UI widgets
│       └── api/                  # HTTP client → :8082
│
├── recorder/                     # Audio capture (Swift, macOS)
│   ├── Sources/MemexRecorder/
│   │   ├── main.swift            # Entry point, arg parsing
│   │   ├── AudioCaptureManager.swift
│   │   ├── SystemAudioCapture.swift   # ScreenCaptureKit
│   │   ├── MicrophoneCapture.swift    # AVAudioEngine
│   │   └── AudioFileWriter.swift      # M4A/WAV output + rotation
│   └── Package.swift
│
├── docs/                         # Documentation
└── logs/                         # Service logs
```

## Key Dependencies

| Component | Dependency | Purpose |
|-----------|-----------|---------|
| Refinery | Tesseract | OCR text extraction |
| Refinery | Pillow, OpenCV | Image processing |
| All | ChromaDB | Vector database + embeddings |
| CLI | Typer + Rich | Terminal UI |
| CLI | anthropic, openai | AI provider SDKs |
| MCP Server | mcp SDK | Model Context Protocol |
| MCP Server | FastAPI + uvicorn | HTTP transport |
| Prometheus | Ollama (llama3.2:1b) | Request validation |
| Prometheus | Cloudflare Tunnel | Public HTTPS access |
| Desktop | Electron + React | Desktop GUI |
| Recorder | ScreenCaptureKit | System audio capture |
| Recorder | AVAudioEngine | Microphone capture |

## Usage Tracking Schema

Every MCP tool call is logged to `~/.memex/usage.jsonl` (local) or `logs/usage.jsonl` (Prometheus):

```jsonl
{"ts":"2026-02-12T10:00:00","event":"tool_call","instance":"personal","tool":"search-screenshots","query_len":42,"results":5,"duration_ms":340}
{"ts":"2026-02-12T10:00:01","event":"tool_call","instance":"personal","tool":"daily-summary","query_len":0,"results":1,"duration_ms":120}
{"ts":"2026-02-12T10:05:00","event":"data_sync","instance":"personal","files":60,"bytes":245760}
```

This is metering-only (no billing logic). Foundation for future subscription and usage-based pricing.
