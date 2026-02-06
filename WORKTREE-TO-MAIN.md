# Getting your worktree/feature branch onto main

## One-time: commit and push your feature branch

1. **Commit everything on your current branch** (e.g. `feature/memex-cli`):

   ```bash
   cd /Users/Joseph.Newbry@alaskaair.com/dev/flow

   git add install.sh README.md   # and any other files you want
   git add -p                      # or add interactively
   git status                      # confirm what will be committed
   git commit -m "Easy install: curl script and memex start/stop"
   ```

2. **Push the feature branch to origin**:

   ```bash
   git push -u origin feature/memex-cli
   ```

## Merge the feature branch into main

3. **Switch to `main` and update it**:

   ```bash
   git checkout main
   git pull origin main
   ```

4. **Merge your feature branch into main**:

   ```bash
   git merge feature/memex-cli -m "Merge feature/memex-cli: easy install and memex CLI"
   ```

5. **Push the updated main**:

   ```bash
   git push origin main
   ```

## Summary

- **Worktree** = a second working directory that shares the same repo and can be on a different branch.
- To get work onto **main**: work on a branch (in a worktree or not) → commit → push branch → checkout main → merge that branch → push main.
- You can delete the worktree when done: from the main repo run  
  `git worktree remove /path/to/worktree`  
  (only if the branch was merged and you don’t need that directory anymore).
