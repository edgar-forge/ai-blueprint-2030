# palantir/ -- Personal Palantir Installer

This directory contains the one-click installer and source files for the Personal Palantir system: an Obsidian-based AI second brain that uses Claude MCP for semantic search, automated nightly note classification, and vault backup/sync automation. Run `setup.sh` and the entire system is configured on your Mac in minutes.

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | any | `npm --version` |
| git | any | `git --version` |
| Claude Code CLI | latest | `claude --version` |
| Obsidian | any | installed and vault created |
| macOS | 12+ | for LaunchAgents (Linux users: use cron instead) |

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/your-username/ai-blueprint-2030.git
cd ai-blueprint-2030/palantir

# 2. Run the installer
chmod +x setup.sh
./setup.sh

# 3. Restart Claude Code to pick up the MCP server
```

The installer will ask for your vault path and Ground Truth file location, then handle everything else.

---

## What Gets Installed

| Component | Location | Purpose |
|-----------|----------|---------|
| MCP Server | `~/obsidian-mcp-server/` | Semantic search via vector embeddings (LanceDB) + Claude MCP integration |
| Python venv | `~/obsidian-mcp-server/venv/` | Isolated Python environment with sentence-transformers, lancedb, mcp |
| Nightly Synapse | `<vault>/scripts/nightly-synapse/` | Auto-classifies today's notes using Claude CLI, generates reports |
| Sync script | `~/ObsidianBackup/sync_from_github.sh` | Bidirectional GitHub sync with .env safety check |
| Backup script | `~/ObsidianBackup/backup_vault.sh` | Daily tar.gz backup with 7-day retention |
| MCP config | `~/.claude/.mcp.json` | Registers the MCP server with Claude Code |
| LaunchAgent: sync | `~/Library/LaunchAgents/com.user.obsidian-github-sync.plist` | Runs sync every 30 minutes |
| LaunchAgent: backup | `~/Library/LaunchAgents/com.user.obsidian-backup.plist` | Runs backup daily at 21:30 |
| LaunchAgent: synapse | `~/Library/LaunchAgents/com.user.nightly-synapse.plist` | Runs classification daily at 21:30 |

---

## Daily Usage

**Semantic search** -- Just ask Claude naturally in Claude Code:

```
"What are my notes about decision-making?"
"Find notes related to system thinking"
```

Claude automatically calls the MCP `search_notes` tool and answers based on your vault.

**Manual indexing** (after adding many notes):

```bash
cd ~/obsidian-mcp-server
./venv/bin/python indexer.py        # incremental (changed notes only)
./venv/bin/python indexer.py --full # full re-index
```

**Manual Nightly Synapse** (run classification now):

```bash
cd <vault>/scripts/nightly-synapse
node run-now.js
```

**Check sync/backup logs**:

```bash
cat ~/ObsidianBackup/sync.log
ls -la ~/ObsidianBackup/ObsidianVault_*.tar.gz
```

---

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| MCP server not showing in Claude Code | Path error in `.mcp.json` | Check `~/.claude/.mcp.json` uses absolute paths (no `~`) |
| MCP server crashes on start | Python packages missing | `~/obsidian-mcp-server/venv/bin/pip install mcp[cli]` |
| Search returns no results | Indexer never ran or vault path wrong | Run `./venv/bin/python indexer.py --full` |
| Search results are stale | Incremental index not running | Re-run indexer or set up a cron/LaunchAgent for it |
| Claude doesn't use the search tool | Claude Code needs restart | Quit and relaunch Claude Code |
| Nightly Synapse fails | Claude CLI not installed | Install Claude Code CLI and verify with `claude --version` |
| Sync script permission denied | Missing execute bit | `chmod +x ~/ObsidianBackup/sync_from_github.sh` |
| LaunchAgent not running | Not loaded or plist error | `launchctl list \| grep com.user` to check; reload with `launchctl load <plist>` |
| Backup too large | .git or cache included | Backup script already excludes .git; check for other large dirs |
| Git push fails | Auth or remote not set | Ensure `git remote -v` shows correct origin and you have push access |

---

## File Structure

```
palantir/
  setup.sh                        # One-click installer
  README.md                       # This file
  backup/
    sync_from_github.sh           # GitHub bidirectional sync (template)
    backup_vault.sh               # Daily backup (template)
  templates/
    CLAUDE.md                     # Template vault rules for users to customize
  obsidian-mcp-server/
    bridge_keywords.py            # Bridge keyword dictionary (template)
    (indexer.py, search.py, server.py are in the guide)
  nightly-synapse/
    package.json                  # Node.js dependencies
    detector.js                   # Modified-note detector
    (classifier.js, synapse.js, report.js, etc. are in the guide)
```

---

## Customization

1. **Bridge keywords** -- Edit `~/obsidian-mcp-server/bridge_keywords.py` with your own themes. Re-run indexer after changes.
2. **Ground Truth** -- Create a classification rules document in your vault. Update the path in `classifier.js`.
3. **CLAUDE.md** -- Copy `templates/CLAUDE.md` to your vault root and customize every section.
4. **Schedules** -- Edit the plist files in `~/Library/LaunchAgents/` to change sync/backup times.
