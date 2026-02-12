# Ideas for Memex Automations

Automations that Memex could run on a schedule or trigger, using screen capture data as input.

## Daily / Recurring

### 1. Daily Standup Summary
- **Schedule:** M-F, 8:30 AM
- **Lookback:** Yesterday (or Friday if Monday)
- **Output:** Formatted standup with "what I worked on" and "what I'm going to work on"
- **Status:** Implemented as `memex standup`

### 2. Weekly Activity Digest
- **Schedule:** Every Friday at 5 PM
- **Lookback:** Mon-Fri of current week
- **Output:** Summary of the week's work, key topics, time distribution across projects

### 3. Daily Screenshot Highlights
- **Schedule:** End of day, 6 PM
- **Lookback:** Today
- **Output:** Curated list of the 5-10 most interesting/unique captures of the day

## Context-Aware

### 4. Meeting Prep Briefing
- **Trigger:** Before calendar events (would need calendar integration)
- **Lookback:** Last 7 days of context related to meeting attendees/topic
- **Output:** Summary of recent work relevant to the meeting

### 5. Context Switch Report
- **Schedule:** End of day
- **Analysis:** Detect topic changes throughout the day (e.g., switched from coding to email to docs)
- **Output:** Timeline of context switches with duration estimates

### 6. Time Tracking Estimate
- **Schedule:** End of day or weekly
- **Analysis:** Which apps, websites, and projects got the most screen time
- **Output:** Breakdown by category (coding, email, meetings, browsing, etc.)

## Extraction

### 7. URL / Bookmark Extraction
- **Schedule:** Daily
- **Analysis:** Extract all URLs visible in browser screenshots
- **Output:** Deduplicated list of URLs visited, saved to a file or bookmark manager

### 8. Knowledge Base Builder
- **Schedule:** Weekly
- **Analysis:** Extract unique insights, learnings, and patterns from the week's captures
- **Output:** Append to a running knowledge base markdown file

### 9. Code Review Summary
- **Schedule:** Daily or on-demand
- **Analysis:** Detect PRs, diffs, and code review interfaces in screenshots
- **Output:** List of PRs reviewed, files changed, review comments made

### 10. Email Draft Assistant
- **Trigger:** On-demand
- **Analysis:** Find email threads visible in recent screenshots
- **Output:** Summary of email thread context to help draft a response
