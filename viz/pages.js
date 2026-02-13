/* ══════════════════════════════════════════════════════════════
   Memex Architecture Visualization — Page Content
   ══════════════════════════════════════════════════════════════ */

const PAGES = {};

/* ── HOME ────────────────────────────────────────────────────── */
PAGES.home = () => `
<div class="page-header">
  <span class="badge badge-blue">Architecture Explorer</span>
  <h2>Memex</h2>
  <p class="subtitle">
    Searchable screen history inspired by Vannevar Bush's 1945 vision.
    Captures screenshots every 60 seconds, extracts text via OCR, indexes in
    a vector database, and exposes everything through MCP tools to Claude and other AI interfaces.
  </p>
</div>

<div class="stat-row">
  <div class="stat"><div class="stat-value" style="color:var(--primary)">60s</div><div class="stat-label">Capture Interval</div></div>
  <div class="stat"><div class="stat-value" style="color:var(--cyan)">8</div><div class="stat-label">MCP Tools</div></div>
  <div class="stat"><div class="stat-value" style="color:var(--green)">525K</div><div class="stat-label">Captures / Year</div></div>
  <div class="stat"><div class="stat-value" style="color:var(--amber)">384d</div><div class="stat-label">Vector Dimensions</div></div>
</div>

<div class="section">
  <h3>Deployment Modes</h3>
  <p>Memex supports three deployment architectures, from personal use to decentralized networks.</p>
</div>

<div class="cards cards-3">
  <div class="card card-link" onclick="location.hash='single'">
    <div class="card-icon" style="color:var(--primary)">&#9673;</div>
    <h3>Single User</h3>
    <p>Local capture, OCR, vector storage, and search. Everything stays on your machine.
       ChromaDB for semantic search, JSON files as durable backup.</p>
    <div class="card-tag" style="background:rgba(129,140,248,0.12);color:var(--primary)">Local &middot; Private</div>
  </div>
  <div class="card card-link" onclick="location.hash='multi'">
    <div class="card-icon" style="color:var(--cyan)">&#9881;</div>
    <h3>Multi-Tenant</h3>
    <p>Multiple user instances on a single server (Prometheus on Jetson Orin Nano).
       Path-based routing, auth, rate limiting, and AI guard models.</p>
    <div class="card-tag" style="background:rgba(34,211,238,0.12);color:var(--cyan)">Shared Server</div>
  </div>
  <div class="card card-link" onclick="location.hash='peer'">
    <div class="card-icon" style="color:var(--green)">&#8942;</div>
    <h3>Multi-Peer</h3>
    <p>Decentralized network of nodes. Cross-node search for job matching,
       skill discovery, and collaborative work history.</p>
    <div class="card-tag" style="background:rgba(52,211,153,0.12);color:var(--green)">Decentralized</div>
  </div>
</div>

<div class="section" style="margin-top:48px">
  <h3>Deep Dives</h3>
  <p>Detailed technical explorations of each subsystem.</p>
</div>

<div class="cards cards-4">
  <div class="card card-link" onclick="location.hash='security'">
    <h3>Security &amp; Vectors</h3>
    <p>Privacy-preserving vector search. Send embeddings without raw text.</p>
  </div>
  <div class="card card-link" onclick="location.hash='dataflow'">
    <h3>Data Flow</h3>
    <p>End-to-end journey from screenshot capture to search result.</p>
  </div>
  <div class="card card-link" onclick="location.hash='mcp'">
    <h3>MCP Architecture</h3>
    <p>Tool inventory, transports, and integration with Claude Desktop.</p>
  </div>
  <div class="card card-link" onclick="location.hash='capture'">
    <h3>Capture Pipeline</h3>
    <p>Screen detection, OCR processing, and storage details.</p>
  </div>
</div>
`;


/* ── SINGLE USER ─────────────────────────────────────────────── */
PAGES.single = () => `
<div class="page-header">
  <span class="badge badge-blue">Architecture</span>
  <h2>Single User</h2>
  <p class="subtitle">
    The core deployment: one machine, fully local. Your screen activity is captured,
    OCR'd, embedded as vectors, and searchable through CLI or AI tools. No data leaves your machine.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Local Architecture</div>
  <div class="mermaid">
graph LR
    subgraph Your Machine
      A["Screen Capture<br/><small>refinery/run.py</small>"] -->|"every 60s"| B["Screenshot<br/><small>PIL / pyautogui</small>"]
      B --> C["Tesseract OCR"]
      C --> D["JSON File<br/><small>data/ocr/*.json</small>"]
      D --> E["ChromaDB<br/><small>:8000</small>"]
      E --> F["Vector<br/>Embeddings"]
    end
    F --> G["MCP Server<br/><small>:8082</small>"]
    G --> H["Claude / Cursor"]
    G --> I["memex CLI"]
  </div>
</div>

<div class="section">
  <h3>Components</h3>
</div>

<div class="cards cards-2">
  <div class="card">
    <h3>Capture Daemon</h3>
    <p><code>refinery/run.py</code> &mdash; Runs as a background process. Every 60 seconds,
    detects all connected screens (macOS, Windows, Linux), takes a screenshot of each,
    runs Tesseract OCR to extract text, and writes a JSON file.</p>
  </div>
  <div class="card">
    <h3>OCR Storage</h3>
    <p><code>refinery/data/ocr/*.json</code> &mdash; One JSON file per capture per screen.
    Filename: <code>{timestamp}_{screen_name}.json</code>. Contains timestamp, screen name,
    full extracted text, word count, and text length.</p>
  </div>
  <div class="card">
    <h3>ChromaDB Vector Database</h3>
    <p>HTTP server on <code>localhost:8000</code>. Collection: <code>screen_ocr_history</code>.
    Each document is embedded using sentence-transformers (384 dimensions).
    Supports semantic search with metadata filtering (date ranges, screen name).</p>
  </div>
  <div class="card">
    <h3>MCP Server</h3>
    <p><code>mcp-server/server.py</code> &mdash; Exposes 8 tools via MCP protocol.
    Supports stdio transport (Claude Desktop) and HTTP transport (<code>:8082</code>)
    for remote access via ngrok.</p>
  </div>
</div>

<div class="section">
  <h3>Dual Storage Strategy</h3>
  <p>Memex uses two complementary storage layers for resilience and flexibility:</p>
</div>

<div class="compare-grid">
  <div class="compare-block good">
    <h4 style="color:var(--green)">JSON Files (Durable)</h4>
    <ul>
      <li>One file per capture, human-readable</li>
      <li>Works without ChromaDB running</li>
      <li>Easy to backup, sync, or grep</li>
      <li>Fallback search via file scanning</li>
      <li>Path: <code>refinery/data/ocr/</code></li>
    </ul>
  </div>
  <div class="compare-block good">
    <h4 style="color:var(--cyan)">ChromaDB (Fast Search)</h4>
    <ul>
      <li>Vector embeddings for semantic search</li>
      <li>Sub-second query response</li>
      <li>Metadata filtering (dates, screens)</li>
      <li>Powers MCP tools and CLI search</li>
      <li>Path: <code>refinery/chroma/</code></li>
    </ul>
  </div>
</div>

<div class="diagram-box">
  <div class="diagram-title">JSON Document Structure</div>
  <pre style="background:transparent;border:none;padding:0;margin:0">{
  "timestamp": "2025-02-13T14-23-45-123456",
  "screen_name": "Display_1",
  "text": "Full OCR text extracted from screenshot...",
  "text_length": 5432,
  "word_count": 890,
  "source": "flow-runner"
}</pre>
</div>

<div class="section">
  <h3>Local Commands</h3>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Command</th><th>Description</th><th>Source</th></tr></thead>
    <tbody>
      <tr><td><code>memex start</code></td><td>Start capture daemon + optional MCP server</td><td>cli/commands/start.py</td></tr>
      <tr><td><code>memex stop</code></td><td>Stop the capture daemon</td><td>cli/commands/stop.py</td></tr>
      <tr><td><code>memex status</code></td><td>Health check (capture, ChromaDB, storage)</td><td>cli/commands/status.py</td></tr>
      <tr><td><code>memex ask "query"</code></td><td>AI-powered semantic search with streaming</td><td>cli/commands/ask.py</td></tr>
      <tr><td><code>memex search "query"</code></td><td>Direct text search (no AI)</td><td>cli/commands/search.py</td></tr>
      <tr><td><code>memex stats</code></td><td>Activity statistics (today, week, month)</td><td>cli/commands/stats.py</td></tr>
      <tr><td><code>memex graph</code></td><td>Terminal dashboard with bar charts</td><td>cli/commands/graph.py</td></tr>
      <tr><td><code>memex sync</code></td><td>Sync OCR JSON files to ChromaDB</td><td>cli/commands/sync.py</td></tr>
      <tr><td><code>memex doctor</code></td><td>Full system diagnostics</td><td>cli/commands/doctor.py</td></tr>
    </tbody>
  </table>
</div>
`;


/* ── MULTI-TENANT ────────────────────────────────────────────── */
PAGES.multi = () => `
<div class="page-header">
  <span class="badge badge-cyan">Architecture</span>
  <h2>Multi-Tenant</h2>
  <p class="subtitle">
    The Prometheus server runs on a Jetson Orin Nano and hosts multiple user instances
    behind a single endpoint. Path-based routing, authentication, rate limiting, and
    AI guard models protect each tenant's data.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Prometheus Multi-Instance Architecture</div>
  <div class="mermaid">
graph TD
    C1["Claude Desktop"] -->|HTTPS| NG["Cloudflare Tunnel<br/><small>memex.digitalsurfacelabs.com</small>"]
    C2["Browser / API"] -->|HTTPS| NG
    NG --> PS["Prometheus Server<br/><small>FastAPI :8082</small>"]
    PS --> AUTH["Auth Layer<br/><small>API Key / Email</small>"]
    AUTH --> RL["Rate Limiter<br/><small>60/min per IP</small>"]
    RL --> GI["AI Guard (Inbound)<br/><small>Ollama Qwen3Guard 0.6B</small>"]
    GI --> IM["Instance Manager"]
    IM --> I1["Personal<br/><small>/personal/mcp</small>"]
    IM --> I2["Walmart<br/><small>/walmart/mcp</small>"]
    IM --> I3["Alaska<br/><small>/alaska/mcp</small>"]
    I1 --> GO["AI Guard (Outbound)<br/><small>PII Scanner</small>"]
    I2 --> GO
    I3 --> GO
    GO --> AL["Audit Log"]
  </div>
</div>

<div class="section">
  <h3>Security Layers</h3>
  <p>Every request passes through five security checkpoints before reaching instance data:</p>
</div>

<div class="flow-steps">
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--primary)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>1. Transport Encryption</h4>
      <p>Cloudflare tunnel provides HTTPS termination. Traffic between client and server is encrypted end-to-end.
         Previously used ngrok; now uses Cloudflare for persistence.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--cyan)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>2. Authentication</h4>
      <p>API key in request header, validated against <code>config/api_keys.env</code>.
         Supports email-based claim verification. Each instance can have different auth rules.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>3. Rate Limiting</h4>
      <p>60 requests/minute per IP, 500 requests/hour per instance. Prevents abuse and
         ensures fair resource sharing across tenants. Configurable per instance.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--amber)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>4. Inbound AI Guard</h4>
      <p>Ollama-hosted Qwen3Guard-Stream 0.6B model validates every incoming request.
         Detects jailbreak attempts, prompt injection, and malicious queries before they reach the tools.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--rose)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>5. Outbound PII Filter</h4>
      <p>Response content is scanned for PII (emails, phone numbers, SSNs, API keys)
         before being returned to the client. Guard model + regex patterns.</p>
    </div>
  </div>
</div>

<div class="section">
  <h3>Instance Routing</h3>
  <p>Each tenant gets a dedicated URL path with isolated data directories:</p>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Instance</th><th>Endpoint</th><th>Data Directory</th><th>ChromaDB Collection</th></tr></thead>
    <tbody>
      <tr><td>Personal</td><td><code>/personal/mcp</code></td><td>/ssd/memex/data/personal/ocr</td><td>personal_ocr</td></tr>
      <tr><td>Walmart</td><td><code>/walmart/mcp</code></td><td>/ssd/memex/data/walmart/ocr</td><td>walmart_ocr</td></tr>
      <tr><td>Alaska</td><td><code>/alaska/mcp</code></td><td>/ssd/memex/data/alaska/ocr</td><td>alaska_ocr</td></tr>
    </tbody>
  </table>
</div>

<div class="section">
  <h3>Hardware: Jetson Orin Nano</h3>
</div>

<div class="cards cards-2">
  <div class="card">
    <h3>System Specs</h3>
    <ul>
      <li>NVIDIA Jetson Orin Nano</li>
      <li>CUDA 12.6, JetPack 6.2.1</li>
      <li>916 GB NVMe SSD at <code>/ssd</code></li>
      <li>781 MB/s write throughput</li>
    </ul>
  </div>
  <div class="card">
    <h3>Running Services</h3>
    <ul>
      <li><code>memex-chromadb</code> &mdash; ChromaDB on :8000</li>
      <li><code>memex-server</code> &mdash; Prometheus on :8082</li>
      <li><code>buddy</code> &mdash; Home assistant on :8001</li>
      <li><code>ollama</code> &mdash; Guard models on :11434</li>
    </ul>
  </div>
</div>

<div class="diagram-box">
  <div class="diagram-title">Audit Log Entry</div>
  <pre style="background:transparent;border:none;padding:0;margin:0">{
  "timestamp": "2025-02-13T14:23:45Z",
  "instance": "personal",
  "method": "tools/call",
  "tool": "search-screenshots",
  "client_ip": "73.xxx.xxx.xxx",
  "query": "kubernetes projects",
  "results_count": 8,
  "pii_filtered": true,
  "guard_passed": true,
  "latency_ms": 342
}</pre>
</div>
`;


/* ── MULTI-PEER ──────────────────────────────────────────────── */
PAGES.peer = () => `
<div class="page-header">
  <span class="badge badge-green">Architecture</span>
  <h2>Multi-Peer Network</h2>
  <p class="subtitle">
    A decentralized network of Memex nodes. Each node captures and indexes its owner's
    screen history locally. Cross-node search enables skill discovery, job matching,
    and collaborative work history &mdash; without centralizing anyone's raw data.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Decentralized Network Topology</div>
  <div class="mermaid">
graph TD
    REG["Discovery Registry<br/><small>Metadata only, no data</small>"]
    REG ---|"register"| N1["Node: Joe's Mac<br/><small>Skills: K8s, Python, AI/ML</small>"]
    REG ---|"register"| N2["Node: Jetson Nano<br/><small>Skills: Edge AI, CUDA</small>"]
    REG ---|"register"| N3["Node: Cloud VM<br/><small>Skills: DevOps, AWS</small>"]
    REG ---|"register"| N4["Node: Alice's Mac<br/><small>Skills: React, TypeScript</small>"]
    S["Searcher / Recruiter"] -->|"1. discover"| REG
    S -->|"2. query"| N1
    S -->|"2. query"| N3
    N1 -.->|"endorse"| N3
    N3 -.->|"endorse"| N1
  </div>
</div>

<div class="section">
  <h3>How Cross-Node Search Works</h3>
</div>

<div class="flow-steps">
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>1. Node Registration</h4>
      <p>Each node publishes metadata to the registry: handle, skills summary, online status,
         and MCP endpoint URL. <strong>No screen data is shared</strong> &mdash; only a capability manifest.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>2. Discovery</h4>
      <p>A recruiter searching for "Kubernetes + Python engineer" queries the registry.
         The registry returns a list of matching nodes with their endpoints and reputation scores.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>3. Direct Query</h4>
      <p>The recruiter's Claude instance connects directly to the candidate's MCP endpoint.
         All standard tools are available: <code>search-screenshots</code>, <code>daily-summary</code>,
         <code>activity-graph</code>. The query flows through the node's security layers.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>4. Filtered Response</h4>
      <p>The node processes the query locally, applies PII filtering, runs the outbound guard model,
         and returns only sanitized results. Raw OCR text and screenshots never leave the machine.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>5. Endorsement</h4>
      <p>Nodes can endorse each other (vouch for quality/reliability). Over time, this builds
         a reputation graph that helps recruiters identify trustworthy candidates.</p>
    </div>
  </div>
</div>

<div class="section">
  <h3>Use Case: Job Matching</h3>
</div>

<div class="diagram-box">
  <div class="diagram-title">Recruiter Search Flow</div>
  <div class="mermaid">
sequenceDiagram
    participant R as Recruiter (Claude)
    participant REG as Registry
    participant N1 as Node: Joe
    participant N2 as Node: Alice
    R->>REG: Find "Kubernetes + Python"
    REG-->>R: [Joe (score 0.92), Alice (score 0.78)]
    R->>N1: search-screenshots("Kubernetes deployment")
    N1->>N1: ChromaDB vector search
    N1->>N1: PII filter + guard model
    N1-->>R: Filtered results (5 matches)
    R->>N2: search-screenshots("Kubernetes deployment")
    N2->>N2: ChromaDB vector search
    N2->>N2: PII filter + guard model
    N2-->>R: Filtered results (3 matches)
    R->>R: Rank candidates by relevance
  </div>
</div>

<div class="section">
  <h3>Decentralization Roadmap</h3>
</div>

<div class="cards cards-2">
  <div class="card">
    <h3 style="color:var(--green)">Phase 1: Registry Network</h3>
    <p>Central registry holds metadata only. Nodes connect via Cloudflare tunnels or ngrok.
       Simple API key auth. Works today with Prometheus architecture.</p>
    <div class="card-tag" style="background:rgba(52,211,153,0.12);color:var(--green)">Current Target</div>
  </div>
  <div class="card">
    <h3 style="color:var(--cyan)">Phase 2: Federated Search</h3>
    <p>Query fan-out to multiple nodes simultaneously. Result aggregation and ranking
       across nodes. Endorsement system for trust scoring.</p>
    <div class="card-tag" style="background:rgba(34,211,238,0.12);color:var(--cyan)">Planned</div>
  </div>
  <div class="card">
    <h3 style="color:var(--amber)">Phase 3: DHT Discovery</h3>
    <p>Replace central registry with a distributed hash table (like BitTorrent DHT).
       No single point of failure. Peer-to-peer node discovery.</p>
    <div class="card-tag" style="background:rgba(251,191,36,0.12);color:var(--amber)">Future</div>
  </div>
  <div class="card">
    <h3 style="color:var(--primary)">Phase 4: Fediverse Integration</h3>
    <p>ActivityPub protocol for node identity. Cross-platform interop with Mastodon-style
       handles. Portable reputation that follows you across platforms.</p>
    <div class="card-tag" style="background:rgba(129,140,248,0.12);color:var(--primary)">Vision</div>
  </div>
</div>

<div class="section">
  <h3>Privacy Guarantees</h3>
  <ul>
    <li><strong>Data sovereignty:</strong> Raw OCR data and screenshots never leave the owner's machine</li>
    <li><strong>Query transparency:</strong> All incoming queries are logged in the audit trail</li>
    <li><strong>Selective sharing:</strong> Node owners choose which time ranges and topics to expose</li>
    <li><strong>Revocable access:</strong> API keys can be rotated or revoked instantly</li>
    <li><strong>Guard model filtering:</strong> AI validates both inbound queries and outbound responses</li>
  </ul>
</div>
`;


/* ── SECURITY & VECTORS ──────────────────────────────────────── */
PAGES.security = () => `
<div class="page-header">
  <span class="badge badge-rose">Deep Dive</span>
  <h2>Security &amp; Vector Storage</h2>
  <p class="subtitle">
    How to enable remote search without exposing raw text. By sending only vector embeddings
    to a remote store, Memex can support cross-node search while keeping OCR data local.
  </p>
</div>

<div class="section">
  <h3>The Problem</h3>
  <p>Memex captures <em>everything</em> on your screen &mdash; passwords, private messages, financial data,
     proprietary code. To enable cross-node search (recruiters, collaborators), we need
     search capability without exposing the underlying text.</p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Current Architecture (Full Data Exposure)</div>
  <div class="mermaid">
graph LR
    subgraph Local Machine
      CAP["Screen Capture"] --> OCR["OCR Text"]
      OCR --> JSON["JSON Files"]
      OCR --> COLL["ChromaDB<br/><small>text + vectors + metadata</small>"]
    end
    COLL -->|"query via MCP"| CLIENT["Remote Client"]
    CLIENT -->|"sees raw text"| RISK["Privacy Risk"]
    style RISK fill:#7f1d1d,stroke:#ef4444,color:#fca5a5
  </div>
</div>

<div class="diagram-box">
  <div class="diagram-title">Proposed: Split Architecture (Vectors Remote, Text Local)</div>
  <div class="mermaid">
graph LR
    subgraph Local Machine
      CAP["Screen Capture"] --> OCR["OCR Text"]
      OCR --> JSON["JSON Files<br/><small>stays local</small>"]
      OCR --> EMB["Embedding Model<br/><small>sentence-transformers</small>"]
      EMB --> LOCAL_DB["Local ChromaDB<br/><small>text + vectors</small>"]
    end
    EMB -->|"vectors + metadata only"| REMOTE["Remote Vector Store<br/><small>no raw text</small>"]
    CLIENT["Remote Searcher"] --> REMOTE
    REMOTE -->|"IDs + similarity scores"| PROXY["Local Proxy"]
    PROXY -->|"fetch text by ID"| LOCAL_DB
    PROXY -->|"PII filter"| CLIENT
    style REMOTE fill:#1e1b4b,stroke:#818cf8,color:#c7d2fe
    style LOCAL_DB fill:#022c22,stroke:#34d399,color:#a7f3d0
  </div>
</div>

<div class="section">
  <h3>How It Works</h3>
</div>

<div class="flow-steps">
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--primary)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>1. Capture &amp; Embed Locally</h4>
      <p>Screenshots are captured and OCR'd as usual. The sentence-transformers model generates
         a 384-dimensional embedding vector for each document. Both the raw text and the vector
         are stored in the local ChromaDB.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--cyan)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>2. Export Vectors to Remote</h4>
      <p>Only the embedding vectors and safe metadata (timestamp, word_count, screen_name)
         are sent to a remote vector store. <strong>Raw OCR text is never transmitted.</strong>
         The remote store holds: <code>[doc_id, vector_384d, timestamp, word_count]</code></p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--green)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>3. Remote Similarity Search</h4>
      <p>A recruiter's query ("Kubernetes experience") is embedded into a vector.
         The remote store performs cosine similarity search and returns
         document IDs + similarity scores. No text is returned at this stage.</p>
    </div>
  </div>
  <div class="flow-step">
    <div class="step-line"><div class="step-dot" style="background:var(--amber)"></div><div class="step-connector"></div></div>
    <div class="step-content">
      <h4>4. Local Text Retrieval</h4>
      <p>The matched document IDs are sent back to the owner's local node.
         The local proxy fetches the actual text from local ChromaDB, applies PII filtering
         via the guard model, and returns sanitized results to the searcher.</p>
    </div>
  </div>
</div>

<div class="section">
  <h3>What Leaks from Vectors?</h3>
  <p>Embedding vectors encode semantic meaning, not exact text. But they aren't perfectly opaque.
     Here's what's known about embedding privacy:</p>
</div>

<div class="compare-grid">
  <div class="compare-block good">
    <h4 style="color:var(--green)">What Vectors Protect</h4>
    <ul>
      <li>Exact text is not recoverable from embeddings</li>
      <li>Specific names, numbers, and credentials are lost</li>
      <li>Character-level details (formatting, code syntax) are abstracted away</li>
      <li>Individual tokens cannot be reliably extracted</li>
    </ul>
  </div>
  <div class="compare-block warn">
    <h4 style="color:var(--amber)">What Vectors Leak</h4>
    <ul>
      <li><strong>Topic:</strong> "This document is about Kubernetes deployment"</li>
      <li><strong>Domain:</strong> "This is code" vs "This is email"</li>
      <li><strong>Approximate content:</strong> Embedding inversion can recover ~60-70% of semantics</li>
      <li><strong>Language &amp; style:</strong> Technical vs casual register</li>
    </ul>
  </div>
</div>

<div class="section">
  <h3>Privacy Enhancement Techniques</h3>
  <p>Five approaches to strengthen privacy beyond the basic split architecture:</p>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Technique</th><th>How It Works</th><th>Privacy Gain</th><th>Search Accuracy</th><th>Complexity</th></tr></thead>
    <tbody>
      <tr>
        <td><strong>1. Vector-Only Federation</strong></td>
        <td>Send embeddings + non-sensitive metadata; keep text local</td>
        <td style="color:var(--green)">High</td>
        <td style="color:var(--green)">Full</td>
        <td style="color:var(--green)">Low</td>
      </tr>
      <tr>
        <td><strong>2. Differential Privacy</strong></td>
        <td>Add calibrated Gaussian noise to vectors before export (epsilon-DP)</td>
        <td style="color:var(--green)">Very High</td>
        <td style="color:var(--amber)">~85-95%</td>
        <td style="color:var(--green)">Low</td>
      </tr>
      <tr>
        <td><strong>3. Random Projection</strong></td>
        <td>Project 384d vectors to lower dimensions (e.g. 128d) via Johnson-Lindenstrauss transform</td>
        <td style="color:var(--green)">High</td>
        <td style="color:var(--amber)">~90%</td>
        <td style="color:var(--green)">Low</td>
      </tr>
      <tr>
        <td><strong>4. LSH Hashing</strong></td>
        <td>Replace vectors with locality-sensitive hash buckets; approximate nearest neighbor</td>
        <td style="color:var(--green)">Very High</td>
        <td style="color:var(--amber)">~80%</td>
        <td style="color:var(--amber)">Medium</td>
      </tr>
      <tr>
        <td><strong>5. Homomorphic Encryption</strong></td>
        <td>Compute cosine similarity on encrypted vectors; never decrypt on server</td>
        <td style="color:var(--green)">Perfect</td>
        <td style="color:var(--green)">Full</td>
        <td style="color:var(--rose)">Very High</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="section">
  <h3>Recommended Approach: Vector Federation + Differential Privacy</h3>
  <p>The most practical combination for Memex is approach 1 + 2:</p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Privacy-Preserving Vector Export Pipeline</div>
  <div class="mermaid">
graph LR
    A["Raw Embedding<br/><small>384 dimensions</small>"] --> B["Add DP Noise<br/><small>epsilon = 1.0</small>"]
    B --> C["Normalize<br/><small>unit length</small>"]
    C --> D["Strip Sensitive<br/>Metadata"]
    D --> E["Export to Remote<br/><small>vector + timestamp +<br/>word_count only</small>"]
    style B fill:#2d1b69,stroke:#818cf8,color:#c7d2fe
  </div>
</div>

<div class="section">
  <h4>Implementation Detail: Noisy Embedding Export</h4>
  <pre>
import numpy as np

def add_dp_noise(embedding, epsilon=1.0):
    """Add differential privacy noise to an embedding vector."""
    sensitivity = 2.0 / len(embedding)  # L2 sensitivity for unit vectors
    noise_scale = sensitivity / epsilon
    noise = np.random.normal(0, noise_scale, len(embedding))
    noisy = embedding + noise
    # Re-normalize to unit length for cosine similarity
    return noisy / np.linalg.norm(noisy)

def export_for_remote(doc_id, embedding, metadata):
    """Prepare a document for remote vector store."""
    safe_metadata = {
        "timestamp": metadata["timestamp"],
        "word_count": metadata.get("word_count", 0),
        "screen_name": metadata.get("screen_name", "unknown"),
        # NO extracted_text, NO raw OCR
    }
    noisy_vec = add_dp_noise(np.array(embedding), epsilon=1.0)
    return {
        "id": doc_id,
        "vector": noisy_vec.tolist(),
        "metadata": safe_metadata
    }</pre>
</div>

<div class="section">
  <h3>ChromaDB: Extracting Vectors Without Text</h3>
  <p>ChromaDB supports getting embeddings separately from documents. Here's how to export
     vectors for remote federation without ever sending text:</p>
  <pre>
import chromadb

client = chromadb.HttpClient(host="localhost", port=8000)
collection = client.get_collection("screen_ocr_history")

# Get embeddings and metadata WITHOUT documents
results = collection.get(
    include=["embeddings", "metadatas"],  # NOT "documents"
    limit=1000,
    offset=0
)

# results["embeddings"] = list of 384-d float vectors
# results["metadatas"]  = list of metadata dicts
# results["ids"]        = list of document IDs
# documents are NOT included — text stays local

for doc_id, emb, meta in zip(results["ids"], results["embeddings"], results["metadatas"]):
    remote_store.upsert(
        id=doc_id,
        vector=add_dp_noise(emb),
        metadata={"timestamp": meta["timestamp"], "word_count": meta.get("word_count", 0)}
    )</pre>
</div>

<div class="section">
  <h3>Remote Vector Store Options</h3>
</div>

<div class="cards cards-3">
  <div class="card">
    <h3>Pinecone</h3>
    <p>Managed vector database. Free tier: 1 index, 100K vectors. Supports metadata filtering.
       Easy API, no infrastructure to manage.</p>
    <div class="card-tag" style="background:rgba(129,140,248,0.12);color:var(--primary)">Managed</div>
  </div>
  <div class="card">
    <h3>Qdrant Cloud</h3>
    <p>Open-source vector DB with cloud hosting. Free tier: 1GB. Supports payload filtering,
       custom scoring, and grouping.</p>
    <div class="card-tag" style="background:rgba(34,211,238,0.12);color:var(--cyan)">Open Source</div>
  </div>
  <div class="card">
    <h3>Self-Hosted ChromaDB</h3>
    <p>Run another ChromaDB instance on a VPS or Jetson. Same API, full control.
       Use the existing Jetson Nano as the remote store.</p>
    <div class="card-tag" style="background:rgba(52,211,153,0.12);color:var(--green)">Self-Hosted</div>
  </div>
</div>

<div class="section">
  <h3>Threat Model</h3>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Threat</th><th>Mitigation</th><th>Residual Risk</th></tr></thead>
    <tbody>
      <tr><td>Remote store compromise</td><td>Vectors + noise only; no text</td><td style="color:var(--green)">Low (topic inference)</td></tr>
      <tr><td>Embedding inversion attack</td><td>DP noise + no text to validate against</td><td style="color:var(--green)">Low</td></tr>
      <tr><td>Metadata correlation</td><td>Only export timestamp + word_count</td><td style="color:var(--green)">Minimal</td></tr>
      <tr><td>Query-response interception</td><td>HTTPS + PII filter on responses</td><td style="color:var(--green)">Low</td></tr>
      <tr><td>Malicious query probing</td><td>AI guard model + rate limiting</td><td style="color:var(--amber)">Medium</td></tr>
      <tr><td>Insider at remote store</td><td>DP noise makes individual docs unrecoverable</td><td style="color:var(--green)">Low</td></tr>
    </tbody>
  </table>
</div>
`;


/* ── DATA FLOW ───────────────────────────────────────────────── */
PAGES.dataflow = () => `
<div class="page-header">
  <span class="badge badge-amber">Deep Dive</span>
  <h2>Data Flow</h2>
  <p class="subtitle">
    The complete journey from a pixel on your screen to a search result in Claude.
    Every 60 seconds, this pipeline runs automatically.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">End-to-End Pipeline</div>
  <div class="mermaid">
graph TD
    S1["All Connected Screens"] -->|"pyautogui<br/>detect displays"| S2["Screen List<br/><small>[Display_1, Display_2]</small>"]
    S2 -->|"PIL screenshot<br/>per screen"| S3["PNG in Memory"]
    S3 -->|"pytesseract<br/>image_to_string"| S4["Raw OCR Text"]
    S4 --> S5["JSON Document"]
    S5 -->|"write to disk"| S6["data/ocr/<br/><small>timestamp_screen.json</small>"]
    S5 -->|"async upsert"| S7["ChromaDB Collection"]
    S7 -->|"sentence-transformers"| S8["384-d Vector<br/>Embedding"]
    S8 --> S9["Indexed &<br/>Searchable"]
  </div>
</div>

<div class="section">
  <h3>Pipeline Timing (Single Capture Cycle)</h3>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Stage</th><th>Duration</th><th>Details</th></tr></thead>
    <tbody>
      <tr><td>Screen detection</td><td>~5ms</td><td>Enumerate displays via pyautogui</td></tr>
      <tr><td>Screenshot capture</td><td>~50-100ms</td><td>PIL grab per screen</td></tr>
      <tr><td>OCR extraction</td><td>~500-2000ms</td><td>Tesseract processing (depends on content density)</td></tr>
      <tr><td>JSON write</td><td>~1ms</td><td>Write to refinery/data/ocr/</td></tr>
      <tr><td>ChromaDB upsert</td><td>~100-300ms</td><td>Generate embedding + store (async)</td></tr>
      <tr><td><strong>Total</strong></td><td><strong>~1-3s</strong></td><td>Per screen, well within the 60s interval</td></tr>
    </tbody>
  </table>
</div>

<div class="section">
  <h3>Query Resolution</h3>
  <p>When a user asks a question, here's how it resolves:</p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Query Flow: "What was I working on yesterday?"</div>
  <div class="mermaid">
sequenceDiagram
    participant U as User (CLI or Claude)
    participant MCP as MCP Server
    participant AI as AI Service
    participant DB as ChromaDB
    participant FS as JSON Files

    U->>MCP: search-recent-relevant("work yesterday")
    MCP->>DB: vector_search(query, time_filter)
    DB->>DB: Embed query → 384-d vector
    DB->>DB: Cosine similarity + metadata filter
    DB-->>MCP: Top 10 results (docs, scores, metadata)
    MCP-->>U: Formatted results

    Note over U,FS: If ChromaDB is unavailable:
    U->>MCP: search-screenshots("work yesterday")
    MCP->>FS: Scan JSON files by date
    FS-->>MCP: Matching documents
    MCP-->>U: Formatted results
  </div>
</div>

<div class="section">
  <h3>Storage Growth</h3>
</div>

<div class="cards cards-3">
  <div class="card">
    <h3>Daily</h3>
    <div class="stat-value" style="color:var(--cyan);font-family:var(--mono);font-size:1.4rem">~1,440</div>
    <p>captures (1 per minute × 24h). Actual count depends on active hours.</p>
  </div>
  <div class="card">
    <h3>Monthly</h3>
    <div class="stat-value" style="color:var(--primary);font-family:var(--mono);font-size:1.4rem">~43K</div>
    <p>captures. JSON files: ~2-5 GB. ChromaDB: ~1-3 GB (with embeddings).</p>
  </div>
  <div class="card">
    <h3>Yearly</h3>
    <div class="stat-value" style="color:var(--green);font-family:var(--mono);font-size:1.4rem">~525K</div>
    <p>captures. JSON files: ~30-60 GB. ChromaDB: ~15-30 GB.</p>
  </div>
</div>

<div class="section">
  <h3>ChromaDB Index Structure</h3>
  <pre>
Collection: "screen_ocr_history"

Document:  "Screen: Display_1 Text: {ocr_text}"
ID:        "{timestamp}_{screen_name}"
Embedding: [0.023, -0.156, 0.089, ... ] (384 floats)
Metadata:
  ├── timestamp       (float)  Unix epoch for range queries
  ├── timestamp_iso   (string) Human-readable ISO format
  ├── screen_name     (string) Display identifier
  ├── text_length     (int)    Character count
  ├── word_count      (int)    Word count
  ├── extracted_text  (string) Full OCR text (for retrieval)
  └── data_type       (string) "ocr"</pre>
</div>

<div class="section">
  <h3>Sync Recovery</h3>
  <p>If ChromaDB goes down or needs rebuilding, the <code>memex sync</code> command re-indexes
     all JSON files:</p>
  <pre>
# Re-index all OCR files into ChromaDB
memex sync

# Flow:
# 1. Scan refinery/data/ocr/*.json
# 2. Parse each JSON file
# 3. Upsert into ChromaDB (skip existing IDs)
# 4. Report: "Synced 52,341 documents in 4m 23s"</pre>
</div>
`;


/* ── MCP ARCHITECTURE ────────────────────────────────────────── */
PAGES.mcp = () => `
<div class="page-header">
  <span class="badge badge-blue">Deep Dive</span>
  <h2>MCP Architecture</h2>
  <p class="subtitle">
    The Model Context Protocol server exposes Memex's capabilities as tools that
    Claude Desktop, Cursor, and other AI interfaces can call directly.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">MCP Transport Modes</div>
  <div class="mermaid">
graph LR
    subgraph "Stdio Transport"
      CD["Claude Desktop"] -->|"stdin/stdout"| SS["server.py<br/><small>MCP SDK</small>"]
    end
    subgraph "HTTP Transport"
      CU["Cursor / Browser"] -->|"HTTP POST"| HS["http_server.py<br/><small>FastAPI :8082</small>"]
      HS --> SS2["FlowMCPServer"]
    end
    subgraph "Remote via Tunnel"
      RC["Remote Client"] -->|"HTTPS"| CF["Cloudflare<br/>Tunnel"]
      CF --> HS
    end
    SS --> DB["ChromaDB<br/><small>:8000</small>"]
    SS2 --> DB
  </div>
</div>

<div class="section">
  <h3>Tool Inventory</h3>
  <p>Eight tools available through MCP, covering search, analytics, and system control:</p>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Tool</th><th>Description</th><th>Key Parameters</th><th>Source</th></tr></thead>
    <tbody>
      <tr>
        <td><code>search-screenshots</code></td>
        <td>Text search across OCR data with date filtering</td>
        <td>query, start_date, end_date, limit</td>
        <td>tools/search.py</td>
      </tr>
      <tr>
        <td><code>vector-search-windowed</code></td>
        <td>Semantic vector search over a time window</td>
        <td>query, hours_back, limit</td>
        <td>tools/vector_search.py</td>
      </tr>
      <tr>
        <td><code>search-recent-relevant</code></td>
        <td>Smart search with recency weighting</td>
        <td>query, limit</td>
        <td>tools/recent_search.py</td>
      </tr>
      <tr>
        <td><code>activity-graph</code></td>
        <td>Activity timeline (hourly or daily grouping)</td>
        <td>period, grouping</td>
        <td>tools/activity.py</td>
      </tr>
      <tr>
        <td><code>time-range-summary</code></td>
        <td>Sampled summary of a time period (24 samples)</td>
        <td>start_date, end_date</td>
        <td>tools/sampling.py</td>
      </tr>
      <tr>
        <td><code>daily-summary</code></td>
        <td>Structured daily report in 6 time periods</td>
        <td>date</td>
        <td>tools/daily_summary.py</td>
      </tr>
      <tr>
        <td><code>sample-time-range</code></td>
        <td>Stratified sampling (min 15-minute windows)</td>
        <td>start, end, n_samples</td>
        <td>tools/sampling.py</td>
      </tr>
      <tr>
        <td><code>get-stats</code></td>
        <td>Statistics: file count, doc count, word count</td>
        <td>(none)</td>
        <td>tools/stats.py</td>
      </tr>
    </tbody>
  </table>
</div>

<div class="section">
  <h3>Server Architecture</h3>
</div>

<div class="diagram-box">
  <div class="diagram-title">MCP Server Class Structure</div>
  <pre style="background:transparent;border:none;padding:0;margin:0">
FlowMCPServer
├── __init__()
│   ├── Connect to ChromaDB (localhost:8000)
│   ├── Get collection "screen_ocr_history"
│   └── Register 8 tools
│
├── list_tools() → List[Tool]
│   └── Returns tool definitions (name, description, schema)
│
├── call_tool(name, arguments) → CallToolResult
│   ├── Dispatch to tool handler
│   ├── Execute ChromaDB query
│   ├── Format results
│   └── Return as MCP content blocks
│
└── Tools
    ├── SearchTool         → text search + date filter
    ├── VectorSearchTool   → semantic similarity search
    ├── RecentSearchTool   → recency-weighted search
    ├── ActivityTool        → timeline aggregation
    ├── SamplingTool        → stratified time sampling
    ├── DailySummaryTool    → structured day reports
    └── StatsTool           → collection statistics</pre>
</div>

<div class="section">
  <h3>Claude Desktop Configuration</h3>
  <p>To connect Claude Desktop to Memex:</p>
  <pre>
// ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "memex": {
      // Option 1: Local stdio (direct Python)
      "command": "python",
      "args": ["/Users/joe/dev/memex/mcp-server/server.py"],

      // Option 2: Remote via tunnel
      // "command": "npx",
      // "args": ["mcp-remote", "https://memex.digitalsurfacelabs.com/sse"]
    }
  }
}</pre>
</div>

<div class="section">
  <h3>Multi-Instance Client</h3>
  <p>The <code>multi_instance_client.py</code> enables a single Claude session to query
     multiple Memex nodes simultaneously:</p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Multi-Instance Fan-Out</div>
  <div class="mermaid">
graph TD
    CLAUDE["Claude Session"] --> MIC["Multi-Instance Client"]
    MIC -->|"/personal/mcp"| I1["Personal Instance"]
    MIC -->|"/walmart/mcp"| I2["Walmart Instance"]
    MIC -->|"/alaska/mcp"| I3["Alaska Instance"]
    I1 --> R["Aggregated Results"]
    I2 --> R
    I3 --> R
    R --> CLAUDE
  </div>
</div>

<div class="section">
  <h3>HTTP Endpoints</h3>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Endpoint</th><th>Method</th><th>Description</th></tr></thead>
    <tbody>
      <tr><td><code>/sse</code></td><td>POST</td><td>MCP Streamable HTTP transport (primary)</td></tr>
      <tr><td><code>/health</code></td><td>GET</td><td>Server health check</td></tr>
      <tr><td><code>/tools</code></td><td>GET</td><td>List available tools (REST fallback)</td></tr>
      <tr><td><code>/search</code></td><td>POST</td><td>Direct search endpoint (REST fallback)</td></tr>
    </tbody>
  </table>
</div>
`;


/* ── CAPTURE PIPELINE ────────────────────────────────────────── */
PAGES.capture = () => `
<div class="page-header">
  <span class="badge badge-amber">Deep Dive</span>
  <h2>Capture Pipeline</h2>
  <p class="subtitle">
    The refinery engine: screen detection, screenshot capture, OCR processing,
    and dual-path storage. Runs continuously as a background daemon.
  </p>
</div>

<div class="diagram-box">
  <div class="diagram-title">Capture Loop Detail</div>
  <div class="mermaid">
graph TD
    START["Daemon Start<br/><small>refinery/run.py</small>"] --> LOOP["Main Loop<br/><small>every 60 seconds</small>"]
    LOOP --> DETECT["Detect Screens<br/><small>lib/screen_detection.py</small>"]
    DETECT --> SCREENS["Screen List"]
    SCREENS --> EACH["For Each Screen"]
    EACH --> SHOT["PIL Screenshot<br/><small>pyscreenshot.grab()</small>"]
    SHOT --> OCR["Tesseract OCR<br/><small>pytesseract.image_to_string()</small>"]
    OCR --> CHECK{"Text Length<br/>> threshold?"}
    CHECK -->|Yes| JSON_W["Write JSON<br/><small>data/ocr/ts_screen.json</small>"]
    CHECK -->|No| SKIP["Skip<br/><small>empty/minimal screen</small>"]
    JSON_W --> CHROMA["Upsert ChromaDB<br/><small>async, non-blocking</small>"]
    CHROMA --> WAIT["Sleep until<br/>next interval"]
    SKIP --> WAIT
    WAIT --> LOOP
  </div>
</div>

<div class="section">
  <h3>Screen Detection</h3>
  <p>Cross-platform screen detection in <code>refinery/lib/screen_detection.py</code>:</p>
</div>

<div class="cards cards-3">
  <div class="card">
    <h3>macOS</h3>
    <p>Uses <code>pyautogui</code> to detect displays. Handles Retina scaling.
       Supports multiple monitors with independent capture.</p>
  </div>
  <div class="card">
    <h3>Windows</h3>
    <p>Win32 API via <code>pyautogui</code>. Handles multi-monitor with different DPI.
       Virtual desktop support.</p>
  </div>
  <div class="card">
    <h3>Linux</h3>
    <p>X11/Xrandr for display enumeration. <code>pyscreenshot</code> as fallback.
       Works on Jetson (headless with virtual framebuffer).</p>
  </div>
</div>

<div class="section">
  <h3>OCR Processing</h3>
</div>

<div class="diagram-box">
  <div class="diagram-title">Tesseract OCR Pipeline</div>
  <div class="mermaid">
graph LR
    A["Screenshot<br/><small>PNG in memory</small>"] --> B["Preprocessing<br/><small>PIL Image</small>"]
    B --> C["Tesseract Engine<br/><small>pytesseract</small>"]
    C --> D["Raw Text<br/><small>with line breaks</small>"]
    D --> E["Text Cleanup<br/><small>strip whitespace</small>"]
    E --> F["Quality Check<br/><small>word count > min</small>"]
    F --> G["JSON + ChromaDB"]
  </div>
</div>

<div class="section">
  <h4>Why Tesseract?</h4>
  <ul>
    <li><strong>Free &amp; open source</strong> &mdash; no API keys, no per-call costs</li>
    <li><strong>Runs locally</strong> &mdash; screenshots never leave the machine</li>
    <li><strong>Good enough</strong> &mdash; ~95% accuracy on screen text (high contrast, clean fonts)</li>
    <li><strong>Fast</strong> &mdash; 0.5-2s per screenshot on modern hardware</li>
  </ul>
</div>

<div class="section">
  <h3>Daemon Management</h3>
</div>

<div class="table-wrap">
  <table>
    <thead><tr><th>Action</th><th>Command</th><th>Details</th></tr></thead>
    <tbody>
      <tr><td>Start</td><td><code>memex start</code></td><td>Launches refinery/run.py as background process. PID stored for management.</td></tr>
      <tr><td>Stop</td><td><code>memex stop</code></td><td>Sends SIGTERM to capture process. Graceful shutdown.</td></tr>
      <tr><td>Status</td><td><code>memex status</code></td><td>Checks: process alive, ChromaDB reachable, disk space, last capture time.</td></tr>
      <tr><td>Watch</td><td><code>memex watch</code></td><td>Live view of captures as they happen. Shows OCR text in real-time.</td></tr>
      <tr><td>Logs</td><td><code>memex logs</code></td><td>Tail capture and MCP server logs.</td></tr>
    </tbody>
  </table>
</div>

<div class="section">
  <h3>File System Layout</h3>
  <pre>
refinery/
├── run.py                         # Main capture loop
├── lib/
│   ├── screen_detection.py        # Cross-platform screen enumeration
│   └── chroma_client.py           # ChromaDB connection manager
├── data/
│   └── ocr/
│       ├── 2025-02-13T08-00-01-123456_Display_1.json
│       ├── 2025-02-13T08-01-01-234567_Display_1.json
│       ├── 2025-02-13T08-01-01-234567_Display_2.json
│       └── ... (~1440 files/day per screen)
├── chroma/                        # ChromaDB persistent storage
│   └── chroma.sqlite3             # SQLite backend
├── logs/
│   └── capture.log                # Daemon log output
├── flow-requirements.txt          # Python dependencies
└── load_ocr_data.py               # Batch re-indexer</pre>
</div>

<div class="section">
  <h3>Systemd Services (Jetson)</h3>
  <p>On the Jetson Orin Nano, capture and ChromaDB run as systemd services:</p>
  <pre>
# /etc/systemd/system/memex-chromadb.service
[Service]
ExecStart=chroma run --host 0.0.0.0 --port 8000 --path /ssd/memex/chroma
WorkingDirectory=/ssd/memex
Restart=always

# /etc/systemd/system/memex-server.service
[Service]
ExecStart=python /ssd/memex/mcp-server/http_server.py
WorkingDirectory=/ssd/memex
Restart=always
Environment=CHROMA_HOST=localhost
Environment=CHROMA_PORT=8000</pre>
</div>
`;


/* ══════════════════════════════════════════════════════════════ */
