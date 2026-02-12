# Do I Need to Build Automations? (Build vs. Buy)

Research on existing tools that could schedule and run Memex-powered automations.

## Existing Options

### Codex Automations
- **What:** Codex (OpenAI's coding agent) has built-in scheduling that runs locally
- **How it works:** Can use MCP tools, so it could connect to the Memex MCP server
- **Pros:** Runs locally, has tool use built in, can chain complex workflows
- **Cons:** Requires an active Codex app session; tied to OpenAI ecosystem
- **Verdict:** Could work for power users already using Codex, but not a general solution

### ClaudeCron
- **What:** MCP server with cron-style scheduling for Claude Code
- **How it works:** Supports bash commands + subagent tasks on a schedule
- **Pros:** Could schedule `memex standup --save` calls; integrates with Claude Code
- **Cons:** Third-party MCP server; requires Claude Code running
- **Verdict:** Good option if you're already in the Claude Code ecosystem

### runCLAUDErun
- **What:** macOS-native app for scheduling Claude Code tasks
- **How it works:** GUI for defining scheduled Claude Code invocations
- **Pros:** macOS-native, nice UI, handles scheduling
- **Cons:** macOS only; third-party app; requires Claude Code subscription
- **Verdict:** Interesting for macOS users, but adds a dependency

### Claude Code + cron / launchd
- **What:** Simple approach using system scheduling
- **How it works:** `claude -p "summarize my day" --allowedTools memex` via crontab or launchd
- **Pros:** No dependencies beyond Claude Code; uses native OS scheduling
- **Cons:** Requires Claude Code CLI; each run is stateless; output goes to stdout
- **Verdict:** Simplest approach for one-off tasks

### Plain launchd / crontab
- **What:** Schedule `memex standup --save` directly
- **How it works:** launchd plist or crontab entry runs the command at specified times
- **Pros:** Zero dependencies; runs as native CLI; output saved to file
- **Cons:** No AI orchestration layer; limited to what the CLI command does
- **Verdict:** Best for well-defined commands like `memex standup`

## Verdict

Existing tools handle *generic* AI scheduling, but none have:
- Memex-specific standup formatting
- Direct integration with Memex's data layer
- Polished output format for standup/digest use cases

**Recommendation:** Build a thin `memex standup` command that encapsulates the standup logic (date lookback, AI prompt, output formatting). Then schedule it with **launchd** (macOS) for reliability and zero dependencies. The generic `memex automate` runner handles custom automations via markdown instruction files.

The scheduling layer is NOT worth building — launchd, cron, ClaudeCron, or any of the above tools handle that perfectly well. The value is in the **command itself** having the right Memex-specific logic.
