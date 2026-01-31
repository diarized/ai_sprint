# Quickstart: AI Sprint System

**Branch**: `001-ai-sprint-system` | **Date**: 2026-01-25
**Purpose**: Get AI Sprint running in under 30 minutes

---

## Prerequisites

Before installing AI Sprint, ensure you have:

- **Python 3.11+**: `python3 --version`
- **Git 2.20+**: `git --version`
- **tmux 3.0+**: `tmux -V`
- **Anthropic API Key**: Get from https://console.anthropic.com/

---

## Installation

### Option 1: pipx (Recommended)

```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
pipx ensurepath

# Install AI Sprint
pipx install ai-sprint
```

### Option 2: pip with venv

```bash
# Create virtual environment
python3 -m venv ~/.ai-sprint-venv
source ~/.ai-sprint-venv/bin/activate

# Install AI Sprint
pip install ai-sprint
```

### Option 3: From Source (Development)

```bash
# Clone repository
git clone https://github.com/yourusername/ai-sprint.git
cd ai-sprint

# Install in development mode
pip install -e ".[dev]"
```

---

## Setup

### 1. Initialize AI Sprint

```bash
# Run installation wizard
ai-sprint install

# Expected output:
# ✓ Created config directory: ~/.ai-sprint/
# ✓ Created database: ~/.ai-sprint/beads.db
# ✓ Created log directory: ~/.ai-sprint/logs/
# ✓ Copied example config: ~/.ai-sprint/ai-sprint.toml
```

### 2. Set API Key

```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export ANTHROPIC_API_KEY="your-api-key-here"

# Reload shell
source ~/.bashrc  # or ~/.zshrc
```

### 3. Verify Installation

```bash
ai-sprint health

# Expected output:
# System Dependencies:
#   ✓ Python 3.11.5
#   ✓ Git 2.42.0
#   ✓ tmux 3.3a
# ...
# Overall: HEALTHY
```

---

## Your First Feature

### 1. Create Feature Specification

You need three files in a specs directory:

```
my-project/
└── specs/
    └── 001-my-feature/
        ├── spec.md      # Feature specification
        ├── plan.md      # Implementation plan
        └── tasks.md     # Task breakdown
```

Use speckit commands to create these:

```bash
# If using speckit
cd my-project
/speckit:specify "Add user authentication"
/speckit:plan
/speckit:tasks
```

Or create them manually following the templates.

### 2. Start Implementation

Note: AI Sprint validates the feature automatically on start.
If validation fails, the feature won't start and you'll get specific error messages.

### 3. Launch the Feature

```bash
# Start the feature
ai-sprint start specs/001-my-feature

# Expected output:
# ✓ Feature validated: 001-my-feature
# ✓ 3 convoys created (5 tasks each)
# ✓ Infrastructure agents started (4)
# ✓ Developer agents spawning (3)
#
# Feature implementation started. Use 'ai-sprint status' to monitor.
```

### 4. Monitor Progress

```bash
# Check status
ai-sprint status

# Watch live updates
ai-sprint status --watch

# View specific agent logs
ai-sprint logs dev-001 --follow
```

### 5. Wait for Completion

AI Sprint runs autonomously. You'll see:

1. **Developers** implementing tasks in parallel
2. **CAB** reviewing code quality
3. **Testers** validating coverage and tests
4. **Refinery** merging to main
5. **Librarian** updating documentation

When complete:
```
Feature Complete: 001-my-feature
================================

Summary:
  ✓ 15 tasks completed
  ✓ 3 convoys merged
  ✓ 0 merge conflicts
  ✓ Documentation updated

Duration: 2h 45m
Tokens used: ~1.2M
```

---

## Common Workflows

### Stopping a Feature

```bash
# Graceful stop (waits for current tasks)
ai-sprint stop

# Force stop (immediate)
ai-sprint stop --force
```

### Resuming a Stopped Feature

```bash
# Just start it again - progress is saved
ai-sprint start specs/001-my-feature
```

### Viewing Logs

```bash
# List all available logs
ai-sprint logs --list

# Main application log
ai-sprint logs

# Specific agent
ai-sprint logs manager

# Follow mode
ai-sprint logs manager --follow

# Last hour only
ai-sprint logs manager --since 1h
```

### Changing Configuration

```bash
# View current config
ai-sprint config show

# Change a setting
ai-sprint config set agents.max_developers 5
ai-sprint config set quality.coverage_threshold 90

# Reset to defaults
ai-sprint config reset --confirm
```

---

## Troubleshooting

### "Feature already running"

```bash
# Check what's running
ai-sprint status

# Stop it if needed
ai-sprint stop
```

### "Agent crashed"

Agents auto-restart. Check logs:

```bash
ai-sprint logs <agent-id> --tail 50
```

### "Task failed 3 times"

Task has been escalated. Check:

```bash
ai-sprint logs manager | grep ESCALATE
```

Manual intervention may be needed.

### "File conflict detected"

Your tasks.md has overlapping files. Fix by:

1. Opening tasks.md
2. Finding conflicting convoys
3. Moving tasks so each file is in only one convoy

### "tmux session not found"

```bash
# List tmux sessions
tmux list-sessions

# Manually kill stuck sessions
tmux kill-server

# Restart AI Sprint
ai-sprint start specs/001-my-feature
```

---

## Configuration Reference

Default configuration in `~/.ai-sprint/ai-sprint.toml`:

```toml
[general]
database_path = "~/.ai-sprint/beads.db"
log_level = "INFO"

[agents]
max_developers = 3          # Parallel developers
max_testers = 3            # Parallel testers
polling_interval_seconds = 30

[timeouts]
agent_heartbeat_seconds = 60    # Health check interval
agent_hung_seconds = 300        # 5 min = hung
task_max_duration_seconds = 7200  # 2 hours max per task

[quality]
coverage_threshold = 80    # Minimum test coverage %
mutation_threshold = 80    # Minimum mutation score %
complexity_max = 15        # Maximum cyclomatic complexity

[security]
critical_cve_max = 0       # Zero tolerance
high_cve_max = 0           # Zero tolerance
medium_cve_max = 5         # Allowed with justification
```

---

## Next Steps

1. **Read the docs**: `docs/architecture.md` for system design
2. **Customize thresholds**: Adjust quality gates to your needs
3. **Integrate with CI**: Add `ai-sprint status --json` to your pipeline
4. **Contribute**: Report issues at https://github.com/yourusername/ai-sprint

---

## Getting Help

- **Health check**: `ai-sprint health`
- **Command help**: `ai-sprint --help`
- **Logs**: `ai-sprint logs all`
- **Issues**: https://github.com/yourusername/ai-sprint/issues
