# Memex CLI - Implementation Plan

> *"Consider a future device... in which an individual stores all his books, records, and communications... mechanized so that it may be consulted with exceeding speed and flexibility."*
> — Vannevar Bush, "As We May Think" (1945)

## Overview

**Memex** - short for "memory extender" - was Vannevar Bush's 1945 vision of a device that would store and retrieve all of a person's information. This CLI brings that vision to life.

```
     ┌─────────────────┐
     │ ═══════════════ │
     │  M E M E X      │
     ├─────────────────┤
     │ ┌─┐ ┌─┐ ┌─┐ ┌─┐ │
     │ └─┘ └─┘ └─┘ └─┘ │
     ├─────────────────┤
     │ ┌─┐ ┌─┐ ┌─┐ ┌─┐ │
     │ └─┘ └─┘ └─┘ └─┘ │
     ├─────────────────┤
     │ ┌─┐ ┌─┐ ┌─┐ ┌─┐ │
     │ └─┘ └─┘ └─┘ └─┘ │
     └─────────────────┘
       "I remember everything"
```

Alternative ASCII (compact):
```
    ┌───────────┐
    │  MEMEX    │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │     memex v1.0.0
    ├───────────┤     ───────────────
    │ ▪ ▪ ▪ ▪   │     "your digital memory"
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    └───────────┘
```

Minimal (for status headers):
```
▣ Memex
```

---

## CLI Design Philosophy

Inspired by Claude Code's visual CLI:
- Rich terminal output with colors and unicode
- Spinners and progress indicators
- Compact but informative output
- Human-readable timestamps and summaries
- No emoji (clean, professional)

---

## Command Structure

```bash
# Primary entry point
memex [command] [options]
```

### Core Commands

| Command | Description |
|---------|-------------|
| `memex status` | Quick health check and current state |
| `memex doctor` | Comprehensive system diagnostics |
| `memex stats` | Show statistics (screenshots today, etc.) |
| `memex search <query>` | Search your history |
| `memex start` | Start capture daemon |
| `memex stop` | Stop capture daemon |
| `memex watch` | Live view of captures |
| `memex config` | View/edit configuration |

---

## Detailed Command Specs

### 1. `memex status`

Quick overview - answers "is everything working?"

```
$ memex status

  ▣ Memex Status
  ─────────────────────────────────────────

  Capture    ● Running     pid 12345
  ChromaDB   ● Connected   localhost:8000
  Storage    ● Healthy     2.3 GB used

  Today: 847 captures across 2 screens
  Last capture: 32 seconds ago

  ─────────────────────────────────────────
```

**Implementation:**
- Check if `run.py` process is running (via pid file or ps)
- Ping ChromaDB
- Count today's OCR files
- Get most recent capture timestamp

---

### 2. `memex doctor`

Comprehensive diagnostics - answers "what's broken and how do I fix it?"

```
$ memex doctor

  ▣ Memex Doctor
  ═══════════════════════════════════════════════════════════

  Dependencies
  ────────────────────────────────────────────────────────────
  ✓ Python 3.11.4         /usr/local/bin/python3
  ✓ Tesseract 5.3.0       /opt/homebrew/bin/tesseract
  ✓ ChromaDB              pip: 0.4.22
  ✗ NGROK                 Not found (optional for remote)

  Services
  ────────────────────────────────────────────────────────────
  ✓ ChromaDB Server       Running on localhost:8000
  ✗ Capture Process       NOT RUNNING
    → Run: memex start

  Permissions
  ────────────────────────────────────────────────────────────
  ✓ Screen Recording      Granted
  ✓ Data Directory        Writable

  Data Integrity
  ────────────────────────────────────────────────────────────
  ✓ OCR Files             12,847 files (98.2% valid)
  ✓ ChromaDB Collection   12,603 documents
  ⚠ Sync Gap              244 files not in ChromaDB
    → Run: memex sync

  Configuration
  ────────────────────────────────────────────────────────────
  ✓ Capture Interval      60s
  ✓ Screens Detected      2 (Built-in, Dell U2720Q)
  ✓ Storage Path          ~/dev/flow/refinery/data/ocr

  ═══════════════════════════════════════════════════════════
  Summary: 1 issue found, 1 warning

  Quick fixes:
    memex start       # Start the capture process
    memex sync        # Sync OCR files to ChromaDB
```

**Implementation:**
- Check each dependency binary exists and version
- Verify services are running
- Check macOS screen recording permission
- Compare OCR file count vs ChromaDB document count
- Validate config values

---

### 3. `memex stats`

Activity statistics with visual flair.

```
$ memex stats

  ▣ Memex Stats
  ─────────────────────────────────────────────────────────────

  Today (Jan 31, 2026)
  ─────────────────────────────────────────────────────────────
  Screenshots: 847           Words captured: 1.2M
  Screens:     2             Avg per hour:   106

  Hours active: ████████████░░░░░░░░░░░░ 8:23 - 17:45
                8  9  10 11 12 13 14 15 16 17 18 19 20

  This Week
  ─────────────────────────────────────────────────────────────
  Mon ████████████████████████████████████████  1,247
  Tue ██████████████████████████████████████    1,189
  Wed ███████████████████████████████           982
  Thu ████████████████████████████████████████  1,256
  Fri █████████████████                         534  (today)
  Sat ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  -
  Sun ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  -

  All Time
  ─────────────────────────────────────────────────────────────
  Total captures:  127,483      Since: Nov 15, 2025
  Total words:     142.3M       Days active: 58
  Storage used:    2.3 GB       Avg/day: 2,198
```

**Flags:**
- `--today` - Only today's stats (default)
- `--week` - This week
- `--month` - This month
- `--all` - All time
- `--json` - Output as JSON

---

### 4. `memex search <query>`

Direct CLI search without needing Claude/Cursor.

```
$ memex search "github pull request"

  ▣ Search: "github pull request"
  ─────────────────────────────────────────────────────────────

  Found 23 matches (showing top 10)

  1. Today 2:34 PM (screen_1)
     ───────────────────────────────────────────────────────────
     ...opened pull request #847: "Add caching layer to API"
     Files changed: 3, +127 -34...

  2. Today 11:15 AM (screen_0)
     ───────────────────────────────────────────────────────────
     ...reviewing PR feedback on authentication changes...

  3. Yesterday 4:45 PM (screen_1)
     ───────────────────────────────────────────────────────────
     ...merged pull request #843 into main branch...

  ─────────────────────────────────────────────────────────────
  Tip: Use --full to see complete text, --export to save results
```

**Flags:**
- `--from <date>` - Start date
- `--to <date>` - End date
- `--screen <name>` - Filter by screen
- `--limit <n>` - Number of results (default 10)
- `--full` - Show full OCR text
- `--export <file>` - Export to file
- `--json` - JSON output

---

### 5. `memex start` / `memex stop`

Daemon management.

```
$ memex start

  ▣ Starting Memex...

  ✓ ChromaDB server started (localhost:8000)
  ✓ Screen capture started (pid 12345)
  ✓ Monitoring 2 screens

  Memex is now recording. Run 'memex status' to check.
```

```
$ memex stop

  ▣ Stopping Memex...

  ✓ Screen capture stopped
  ✓ ChromaDB server stopped

  Today's session: 847 captures over 8h 23m
```

**Flags:**
- `--foreground` / `-f` - Run in foreground with live output
- `--no-chroma` - Don't auto-start ChromaDB
- `--screens <list>` - Only capture specific screens

---

### 6. `memex watch`

Live view of captures (like `tail -f` for your screen history).

```
$ memex watch

  ▣ Memex Watch (live)
  ─────────────────────────────────────────────────────────────

  17:45:32 │ screen_0 │ 234 words │ "VS Code - cli-for-memex..."
  17:46:32 │ screen_1 │ 189 words │ "Chrome - GitHub Pull Req..."
  17:47:32 │ screen_0 │ 256 words │ "VS Code - terminal outpu..."
  17:48:32 │ screen_1 │ 178 words │ "Slack - #engineering cha..."
  █

  Press q to quit, s for stats, p to pause
```

---

### 7. `memex config`

View and manage configuration.

```
$ memex config

  ▣ Memex Configuration
  ─────────────────────────────────────────────────────────────

  capture_interval   60        Seconds between captures
  data_path          ~/dev/flow/refinery/data/ocr
  chroma_host        localhost
  chroma_port        8000
  screens            all       (2 detected)
  retention_days     365       Auto-delete after (0=never)

  Edit: memex config set <key> <value>
  File: ~/.memex/config.toml
```

---

### 8. `memex sync`

Sync OCR files to ChromaDB (recovery/maintenance).

```
$ memex sync

  ▣ Syncing to ChromaDB...

  Scanning OCR files... 12,847 found
  Checking ChromaDB...   12,603 indexed

  Syncing 244 missing documents...
  ████████████████████████████████████████ 100%

  ✓ Sync complete. 244 documents added.
```

---

## File Structure

```
flow/
├── cli/
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── main.py              # CLI app (click/typer)
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── status.py
│   │   ├── doctor.py
│   │   ├── stats.py
│   │   ├── search.py
│   │   ├── start.py
│   │   ├── stop.py
│   │   ├── watch.py
│   │   ├── config.py
│   │   └── sync.py
│   ├── display/
│   │   ├── __init__.py
│   │   ├── colors.py        # Color schemes
│   │   ├── components.py    # Reusable UI components
│   │   ├── spinners.py      # Progress indicators
│   │   └── charts.py        # ASCII charts/graphs
│   ├── services/
│   │   ├── __init__.py
│   │   ├── capture.py       # Interface with refinery
│   │   ├── database.py      # Interface with ChromaDB
│   │   ├── health.py        # Health checks
│   │   └── search.py        # Search functionality
│   └── config/
│       ├── __init__.py
│       ├── settings.py      # Config management
│       └── defaults.py      # Default values
├── pyproject.toml           # Add CLI entry point
└── ...
```

---

## Dependencies

```toml
# pyproject.toml additions
[project.scripts]
memex = "cli.main:app"

[project.optional-dependencies]
cli = [
    "typer[all]>=0.9.0",    # CLI framework
    "rich>=13.0.0",          # Rich terminal output
    "humanize>=4.0.0",       # Human-readable numbers/dates
]
```

---

## Implementation Phases

### Phase 1: Foundation (Core Infrastructure)
- [ ] Create `cli/` directory structure
- [ ] Set up Typer app with Rich integration
- [ ] Implement display components (colors, spinners, tables)
- [ ] Add `memex --version` and `memex --help`
- [ ] Create service interfaces for refinery/ChromaDB

### Phase 2: Status & Doctor (Quick Wins)
- [ ] Implement `memex status`
- [ ] Implement `memex doctor`
- [ ] Add health check utilities
- [ ] Test on macOS

### Phase 3: Stats & Search (Core Value)
- [ ] Implement `memex stats` with charts
- [ ] Implement `memex search` with highlighting
- [ ] Add date parsing (natural language: "yesterday", "last week")
- [ ] Export functionality

### Phase 4: Daemon Management
- [ ] Implement `memex start` with process management
- [ ] Implement `memex stop`
- [ ] PID file management
- [ ] Graceful shutdown handling

### Phase 5: Advanced Features
- [ ] Implement `memex watch` (live view)
- [ ] Implement `memex config`
- [ ] Implement `memex sync`
- [ ] Add shell completions (bash, zsh, fish)

### Phase 6: Polish
- [ ] Add `--json` output to all commands
- [ ] Comprehensive error messages with fix suggestions
- [ ] Man page generation
- [ ] Homebrew formula (future)

---

## Visual Design System

### Colors
```python
COLORS = {
    "primary": "#3B82F6",      # Blue (filing cabinet / professional)
    "success": "#10B981",      # Green
    "warning": "#F59E0B",      # Amber
    "error": "#EF4444",        # Red
    "muted": "#6B7280",        # Gray
    "text": "#F3F4F6",         # Light gray
}
```

### Status Indicators
```
●  Running / Success (green)
○  Stopped / Inactive (gray)
◐  In progress / Partial (yellow)
✗  Error / Failed (red)
⚠  Warning (amber)
```

### The Memex Logo
For the CLI header, use a minimal version:
```
▣ Memex
```

For `--help` and startup, optionally show:
```
    ┌───────────┐
    │  MEMEX    │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │     memex v1.0.0
    ├───────────┤     ───────────────
    │ ▪ ▪ ▪ ▪   │     "your digital memory"
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    └───────────┘
```

---

## Example Session

```bash
$ memex

    ┌───────────┐
    │  MEMEX    │
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │     memex v1.0.0
    ├───────────┤     ───────────────
    │ ▪ ▪ ▪ ▪   │     "your digital memory"
    ├───────────┤
    │ ▪ ▪ ▪ ▪   │
    └───────────┘

Usage: memex [command] [options]

Commands:
  status    Quick health check
  doctor    Full system diagnostics
  stats     Activity statistics
  search    Search your history
  start     Start capture daemon
  stop      Stop capture daemon
  watch     Live capture view
  config    View/edit settings
  sync      Sync files to database

Run 'memex <command> --help' for command details.
```

---

## Future Ideas

- **memex summary** - AI-generated summary of your day/week
- **memex export** - Export data to various formats
- **memex clean** - Remove old data
- **memex backup** - Backup to cloud storage
- **memex web** - Launch local web UI
- **TUI mode** - Full terminal UI with navigation

---

## Questions to Resolve

1. **Config location**: `~/.memex/` vs `~/.config/memex/` vs in project?
2. **Process management**: Use systemd/launchd or simple pid files?
3. **Should start/stop manage ChromaDB separately or together?**
4. **Natural language dates**: Build or use library (parsedatetime)?
