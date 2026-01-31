# CLI Commands Contract: AI Sprint System

**Branch**: `001-ai-sprint-system` | **Date**: 2026-01-25
**Purpose**: Define CLI interface for AI Sprint

---

## Command Overview

```
ai-sprint
├── start <feature-dir>     # Start implementing a feature
├── stop [--force]          # Stop current implementation
├── status                  # Show current status
├── health                  # Check system health
├── install                 # Install/verify dependencies
├── config                  # Manage configuration
│   ├── show               # Show current config
│   ├── set <key> <value>  # Set config value
│   └── reset              # Reset to defaults
└── logs                    # View logs
    ├── manager            # Manager agent logs
    ├── cab                # CAB agent logs
    ├── refinery           # Refinery agent logs
    ├── librarian          # Librarian agent logs
    └── all                # All agent logs
```

---

## Command Specifications

### ai-sprint start

**Purpose**: Start implementing a feature from specification

**Usage**:
```bash
ai-sprint start <feature-dir> [OPTIONS]
```

**Arguments**:

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| feature-dir | path | Yes | Path to specs directory containing spec.md, plan.md, tasks.md |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --dry-run | flag | false | Validate feature without starting |
| --max-developers | int | 3 | Maximum parallel developers |
| --max-testers | int | 3 | Maximum parallel testers |
| --verbose / -v | flag | false | Verbose output |

**Behavior**:
1. Validate feature-dir contains required files
2. Validate no file conflicts between convoys
3. Register feature in database
4. Start permanent agents (manager, cab, refinery, librarian)
5. Manager creates convoys and spawns developers
6. Return immediately (agents run in background)

**Output** (success):
```
✓ Feature validated: 001-ai-sprint-system
✓ 3 convoys created (5 tasks each)
✓ Infrastructure agents started (4)
✓ Developer agents spawning (3)

Feature implementation started. Use 'ai-sprint status' to monitor.
```

**Output** (validation error):
```
✗ Validation failed:

  File conflict detected between convoys:
  - convoy-us1: src/auth/session.ts
  - convoy-us2: src/auth/session.ts

  Resolve file overlap in tasks.md before starting.
```

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Validation error |
| 2 | Feature already running |
| 3 | System dependency missing |

---

### ai-sprint stop

**Purpose**: Stop current feature implementation

**Usage**:
```bash
ai-sprint stop [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --force | flag | false | Stop without graceful shutdown |
| --timeout | int | 30 | Seconds to wait for graceful stop |

**Behavior**:
1. Send stop signal to all agents
2. Wait for graceful shutdown (or force if timeout)
3. Clean up worktrees
4. Mark feature as stopped (can resume later)

**Output**:
```
Stopping AI Sprint...
  ✓ Developer agents stopped (3)
  ✓ Tester agents stopped (2)
  ✓ Infrastructure agents stopped (4)
  ✓ Worktrees cleaned (3)

Feature paused. Progress saved. Use 'ai-sprint start' to resume.
```

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No feature running |
| 2 | Force stop required |

---

### ai-sprint status

**Purpose**: Show current implementation status

**Usage**:
```bash
ai-sprint status [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --json | flag | false | Output as JSON |
| --watch / -w | flag | false | Continuous update (every 5s) |

**Output** (table format):
```
AI Sprint Status
================

Feature: 001-ai-sprint-system
Status:  in_progress
Started: 2026-01-25 10:30:00

Convoys:
┌──────────────┬──────────┬──────────┬───────────┬──────────┐
│ Convoy       │ Priority │ Status   │ Assignee  │ Progress │
├──────────────┼──────────┼──────────┼───────────┼──────────┤
│ convoy-us1   │ P1       │ done     │ dev-001   │ 5/5      │
│ convoy-us2   │ P1       │ progress │ dev-002   │ 3/5      │
│ convoy-us3   │ P2       │ progress │ dev-003   │ 1/5      │
└──────────────┴──────────┴──────────┴───────────┴──────────┘

Agents:
┌───────────┬──────────┬────────────────┬────────────┐
│ Agent     │ Status   │ Current Task   │ Heartbeat  │
├───────────┼──────────┼────────────────┼────────────┤
│ manager   │ active   │ -              │ 5s ago     │
│ cab       │ active   │ -              │ 3s ago     │
│ refinery  │ active   │ -              │ 8s ago     │
│ librarian │ active   │ -              │ 12s ago    │
│ dev-001   │ active   │ -              │ 2s ago     │
│ dev-002   │ active   │ T008           │ 1s ago     │
│ dev-003   │ active   │ T011           │ 4s ago     │
└───────────┴──────────┴────────────────┴────────────┘

Tasks In Progress:
┌────────┬─────────────────────────────────┬───────────┬──────────┐
│ Task   │ Title                           │ Status    │ Duration │
├────────┼─────────────────────────────────┼───────────┼──────────┤
│ T008   │ Implement auth middleware       │ in_review │ 45m      │
│ T011   │ Add rate limiting               │ in_tests  │ 20m      │
└────────┴─────────────────────────────────┴───────────┴──────────┘
```

**Output** (JSON format):
```json
{
  "feature": {
    "id": "001-ai-sprint-system",
    "status": "in_progress",
    "started_at": "2026-01-25T10:30:00Z"
  },
  "convoys": [
    {
      "id": "convoy-us1",
      "priority": "P1",
      "status": "done",
      "assignee": "dev-001",
      "tasks_done": 5,
      "tasks_total": 5
    }
  ],
  "agents": [
    {
      "id": "manager",
      "status": "active",
      "last_heartbeat": "2026-01-25T11:15:55Z"
    }
  ]
}
```

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | No feature running |

---

### ai-sprint health

**Purpose**: Check system health and dependencies

**Usage**:
```bash
ai-sprint health [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --fix | flag | false | Attempt to fix issues |
| --json | flag | false | Output as JSON |

**Output**:
```
AI Sprint Health Check
======================

System Dependencies:
  ✓ Python 3.11.5
  ✓ Git 2.42.0
  ✓ tmux 3.3a
  ✓ SQLite 3.40.1

Python Packages:
  ✓ click 8.1.7
  ✓ gitpython 3.1.40
  ✓ libtmux 0.37.0
  ✓ pydantic 2.5.2
  ✓ rich 13.7.0

Quality Tools:
  ✓ ruff 0.4.1
  ✓ mypy 1.10.0
  ✓ pytest 8.0.0
  ⚠ mutmut not installed (optional)
  ⚠ semgrep not installed (optional)
  ⚠ trivy not installed (optional)

Database:
  ✓ Database exists: ~/.ai-sprint/beads.db
  ✓ Schema version: 1

Overall: HEALTHY (2 optional tools missing)
```

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | Healthy (required deps OK) |
| 1 | Unhealthy (missing required deps) |

---

### ai-sprint install

**Purpose**: Install or verify dependencies

**Usage**:
```bash
ai-sprint install [OPTIONS]
```

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --all | flag | false | Install optional tools too |
| --upgrade | flag | false | Upgrade existing packages |

**Behavior**:
1. Check Python version
2. Install required Python packages
3. Initialize database if needed
4. Create config directory
5. Optionally install quality tools

**Output**:
```
Installing AI Sprint dependencies...

  ✓ Created config directory: ~/.ai-sprint/
  ✓ Created database: ~/.ai-sprint/beads.db
  ✓ Created log directory: ~/.ai-sprint/logs/
  ✓ Copied example config: ~/.ai-sprint/ai-sprint.toml

Installation complete. Run 'ai-sprint health' to verify.
```

**Exit Codes**:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Installation failed |

---

### ai-sprint config

**Purpose**: Manage configuration

#### ai-sprint config show

**Usage**:
```bash
ai-sprint config show [--section <section>]
```

**Output**:
```
AI Sprint Configuration
=======================

[general]
database_path = ~/.ai-sprint/beads.db
log_level = INFO

[agents]
max_developers = 3
max_testers = 3
polling_interval_seconds = 30

[quality]
coverage_threshold = 80
mutation_threshold = 80
complexity_max = 15

[security]
critical_cve_max = 0
high_cve_max = 0
```

#### ai-sprint config set

**Usage**:
```bash
ai-sprint config set <key> <value>
```

**Examples**:
```bash
ai-sprint config set agents.max_developers 5
ai-sprint config set quality.coverage_threshold 90
```

#### ai-sprint config reset

**Usage**:
```bash
ai-sprint config reset [--confirm]
```

---

### ai-sprint logs

**Purpose**: View agent logs

**Usage**:
```bash
ai-sprint logs <agent> [OPTIONS]
```

**Arguments**:

| Argument | Values | Description |
|----------|--------|-------------|
| agent | manager, cab, refinery, librarian, dev-{n}, tester-{n}, all | Which agent's logs |

**Options**:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| --tail / -n | int | 100 | Number of lines |
| --follow / -f | flag | false | Follow log output |
| --since | string | - | Show logs since (e.g., "1h", "2d") |

**Output**:
```
[2026-01-25 10:30:15] [manager] INFO: Starting feature: 001-ai-sprint-system
[2026-01-25 10:30:16] [manager] INFO: Created convoy: convoy-us1 (5 tasks)
[2026-01-25 10:30:17] [manager] INFO: Spawning developer: dev-001
[2026-01-25 10:30:18] [dev-001] INFO: Claimed convoy: convoy-us1
[2026-01-25 10:30:20] [dev-001] INFO: Starting task: T001
```

---

## Error Messages

### Validation Errors

| Error Code | Message | Resolution |
|------------|---------|------------|
| E001 | "spec.md not found in {path}" | Create spec.md |
| E002 | "plan.md not found in {path}" | Run /speckit:plan |
| E003 | "tasks.md not found in {path}" | Run /speckit:tasks |
| E004 | "File conflict: {files}" | Reorganize tasks to avoid overlap |
| E005 | "Circular dependency: {convoys}" | Remove circular convoy dependencies |

### Runtime Errors

| Error Code | Message | Resolution |
|------------|---------|------------|
| R001 | "Feature already running" | Stop current feature first |
| R002 | "Agent {id} crashed" | Check logs, will auto-restart |
| R003 | "Task {id} failed {n} times" | Check escalation in logs |
| R004 | "Merge conflict detected" | Manual resolution required |
| R005 | "API rate limit exceeded" | Wait or increase limits |

### System Errors

| Error Code | Message | Resolution |
|------------|---------|------------|
| S001 | "tmux not available" | Install tmux |
| S002 | "Git worktree failed" | Check git version |
| S003 | "Database locked" | Wait or force stop |
| S004 | "Insufficient permissions" | Check file permissions |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| AI_SPRINT_CONFIG | Config file path | ~/.ai-sprint/ai-sprint.toml |
| AI_SPRINT_DATABASE | Database path | ~/.ai-sprint/beads.db |
| AI_SPRINT_LOG_LEVEL | Log verbosity | INFO |
| ANTHROPIC_API_KEY | Claude API key | (required) |
