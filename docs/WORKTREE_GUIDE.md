# Git Worktrees with Claude Code

## What Is a Git Worktree?

A git worktree lets you check out multiple branches of the same repository
into different directories — simultaneously. Each directory has its own
working tree, but they all share the same `.git` history.

```mermaid
graph TD
    subgraph "Shared Git Repository"
        GIT[".git directory<br/>(single source of truth)"]
    end

    subgraph "Worktree 1: ~/dev/flow"
        WT1["Branch: main<br/>Your primary working directory"]
    end

    subgraph "Worktree 2: ~/dev/flow-security"
        WT2["Branch: feature/security-middleware<br/>Working on security layer"]
    end

    subgraph "Worktree 3: ~/dev/flow-decentralized"
        WT3["Branch: feature/decentralized<br/>Working on P2P discovery"]
    end

    GIT --> WT1
    GIT --> WT2
    GIT --> WT3
```

## Why Use Worktrees?

Without worktrees, switching branches means:
- Stashing or committing unfinished work
- Waiting for `node_modules` / `.venv` to rebuild
- Losing your mental context
- One Claude Code session blocks another

With worktrees:
- Each branch lives in its own folder
- No stashing, no rebuilding
- Run Claude Code in each folder independently
- Work on multiple features in parallel

## How to Create a Worktree

```bash
# You're in ~/dev/flow on the main branch

# Create a worktree for a new branch
git worktree add ../flow-security -b feature/security-middleware

# Create a worktree for an existing branch
git worktree add ../flow-hotfix bugfix/fix-auth

# List all worktrees
git worktree list
# ~/dev/flow                  abc1234 [main]
# ~/dev/flow-security         abc1234 [feature/security-middleware]
# ~/dev/flow-hotfix           def5678 [bugfix/fix-auth]
```

## Running Claude Code in Multiple Worktrees

Each worktree is a separate directory, so you can run a separate Claude Code
session in each one. They are completely independent.

```mermaid
graph LR
    subgraph "Terminal 1"
        CC1["Claude Code<br/>~/dev/flow<br/>(main branch)"]
    end

    subgraph "Terminal 2"
        CC2["Claude Code<br/>~/dev/flow-security<br/>(security branch)"]
    end

    subgraph "Terminal 3"
        CC3["Claude Code<br/>~/dev/flow-decentralized<br/>(decentralized branch)"]
    end

    subgraph "Shared .git"
        GIT["Git Objects<br/>Commits, Blobs, Trees"]
    end

    CC1 -.->|reads/writes| GIT
    CC2 -.->|reads/writes| GIT
    CC3 -.->|reads/writes| GIT
```

### What's Shared vs. Independent

```mermaid
graph TD
    subgraph "SHARED across all worktrees"
        S1["Git history (commits, branches, tags)"]
        S2["Remote tracking (origin/main, etc.)"]
        S3["Git config (.git/config)"]
        S4["Hooks (.git/hooks/)"]
    end

    subgraph "INDEPENDENT per worktree"
        I1["Working directory files"]
        I2["Staged changes (index)"]
        I3["HEAD (current branch)"]
        I4["Untracked files"]
        I5[".venv / node_modules"]
        I6["Claude Code session context"]
    end

    style S1 fill:#e8f5e9
    style S2 fill:#e8f5e9
    style S3 fill:#e8f5e9
    style S4 fill:#e8f5e9
    style I1 fill:#e3f2fd
    style I2 fill:#e3f2fd
    style I3 fill:#e3f2fd
    style I4 fill:#e3f2fd
    style I5 fill:#e3f2fd
    style I6 fill:#e3f2fd
```

## How Conflicts Get Resolved

The key question: what happens when two worktrees (and two Claude Code sessions)
modify the same repository?

### Scenario 1: Working on Different Branches (Normal Case)

```mermaid
sequenceDiagram
    participant WT1 as Worktree 1 (main)
    participant GIT as Shared .git
    participant WT2 as Worktree 2 (feature/security)

    WT1->>GIT: commit "update README"
    WT2->>GIT: commit "add middleware"
    Note over GIT: No conflict!<br/>Different branches,<br/>different commit chains

    WT2->>GIT: git merge main
    Note over GIT: Merge brings README<br/>update into feature branch
```

**No conflict.** Each worktree commits to its own branch. Merging happens
when you're ready, either via `git merge` or a pull request.

### Scenario 2: Both Worktrees on the Same Branch

**Git prevents this.** You cannot have two worktrees checked out to the same
branch. If you try:

```bash
# In ~/dev/flow (on main)
git worktree add ../flow-copy main
# fatal: 'main' is already checked out at '~/dev/flow'
```

This is a safety feature. One branch = one worktree.

### Scenario 3: Merge Conflicts at PR Time

```mermaid
sequenceDiagram
    participant F1 as feature/security
    participant MAIN as main
    participant F2 as feature/decentralized

    F1->>MAIN: PR #1: Merge security branch
    Note over MAIN: main now has<br/>security middleware

    F2->>MAIN: PR #2: Merge decentralized branch
    Note over MAIN: CONFLICT!<br/>Both modified http_server.py

    MAIN-->>F2: Resolve conflicts in PR #2
    Note over F2: Update branch,<br/>fix conflicts,<br/>re-push
```

**This is normal git workflow.** Worktrees don't change how merge conflicts
work — they just let you work on both features simultaneously without switching.

### Scenario 4: Rebasing a Worktree

```bash
# In ~/dev/flow-security (feature/security branch)
git fetch origin
git rebase origin/main

# If there are conflicts, resolve them here
# The other worktree (~/dev/flow) is unaffected
```

Each worktree resolves its own conflicts independently.

## Practical Workflow with Claude Code

### Step 1: Set Up Worktrees

```bash
cd ~/dev/flow

# Create worktrees for each feature
git worktree add ../flow-security -b feature/security-middleware
git worktree add ../flow-decentralized -b feature/decentralized-network
```

### Step 2: Run Claude Code in Each

```bash
# Terminal 1
cd ~/dev/flow-security
claude

# Terminal 2
cd ~/dev/flow-decentralized
claude
```

### Step 3: Each Claude Code Session Sees Its Own Branch

- Terminal 1's Claude Code sees `feature/security-middleware` files
- Terminal 2's Claude Code sees `feature/decentralized-network` files
- Neither session interferes with the other
- Both can commit, push, and create PRs independently

### Step 4: Merge When Ready

```bash
# Create PRs from each worktree
cd ~/dev/flow-security
gh pr create --title "Add security middleware"

cd ~/dev/flow-decentralized
gh pr create --title "Add decentralized discovery"

# Merge PR #1 first, then rebase PR #2
```

### Step 5: Clean Up Worktrees

```bash
# After merging, remove the worktree
git worktree remove ../flow-security

# Or force remove if there are untracked files
git worktree remove --force ../flow-security

# Prune stale worktree references
git worktree prune
```

## CLAUDE.md and Worktrees

Each worktree can have its own `CLAUDE.md` file at the root. This is useful for
giving each Claude Code session branch-specific context:

```
~/dev/flow/CLAUDE.md           → "You're on main. Don't break anything."
~/dev/flow-security/CLAUDE.md  → "You're building the security middleware."
~/dev/flow-decentral/CLAUDE.md → "You're building the P2P discovery layer."
```

Claude Code reads `CLAUDE.md` from the working directory, so each session
automatically gets the right context.

## Common Gotchas

### 1. Virtual Environments

Each worktree needs its own `.venv` if you're running Python:

```bash
cd ~/dev/flow-security
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Add `.venv` to `.gitignore` so it's not tracked.

### 2. Ports

If both worktrees try to start services on the same port (e.g., ChromaDB on 8000),
one will fail. Use different ports per worktree or only run services in one.

### 3. Lockfiles

Git operations that modify `.git/` (like `git gc`, `git prune`) affect all
worktrees. Don't run these while another worktree is mid-operation.

### 4. Branch Deletion

You can't delete a branch that has an active worktree. Remove the worktree first:

```bash
git worktree remove ../flow-security
git branch -d feature/security-middleware
```

## Summary

```mermaid
flowchart TD
    START["You have a repo at ~/dev/flow"]
    START --> CREATE["git worktree add ../flow-feature -b feature/x"]
    CREATE --> CLAUDE["Run 'claude' in ~/dev/flow-feature"]
    CLAUDE --> WORK["Claude Code works independently<br/>on the feature branch"]
    WORK --> COMMIT["Commits go to feature/x branch"]
    COMMIT --> PR["Create PR: gh pr create"]
    PR --> MERGE["Merge PR into main"]
    MERGE --> CLEAN["git worktree remove ../flow-feature"]
    CLEAN --> DONE["Done! Branch merged, worktree gone"]

    style START fill:#fff3e0
    style DONE fill:#e8f5e9
```

Worktrees + Claude Code = parallel feature development without context switching.
Each Claude Code session lives in its own directory, on its own branch, with its
own context. They share git history but nothing else. Conflicts resolve at merge
time, just like normal git.
