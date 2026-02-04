# Architecture: AI Sprint

Technical architecture and system design overview.

## System Overview

AI Sprint is a multi-agent orchestration system that autonomously implements software features from specification through to deployment. The system coordinates 9 agent types (4 permanent infrastructure + 5 on-demand workers) using Git worktree isolation, SQLite-based state management, and quality gates.

### Core Principles

1. **Autonomous Execution**: No human intervention from spec to merge
2. **Conflict Prevention**: Git worktree isolation prevents merge conflicts
3. **Quality Enforcement**: Multi-layer quality gates ensure code standards
4. **Fault Tolerance**: Automatic crash recovery with state preservation
5. **Observability**: Rich logging and tmux session inspection

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Sprint CLI                             │
│                   (Click-based commands)                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Manager Agent (Permanent)                     │
│  • Polls SQLite for ready features                              │
│  • Creates convoys from tasks.md                                │
│  • Spawns Developer/Tester agents via tmux                      │
│  • Monitors health, restarts crashed agents                     │
└───────────────┬──────────────────────┬──────────────────────────┘
                │                      │
       ┌────────┴────────┐    ┌───────┴────────┐
       │                 │    │                 │
       ▼                 ▼    ▼                 ▼
┌──────────┐      ┌──────────┐ ┌──────────┐ ┌──────────┐
│   CAB    │      │ Refinery │ │Librarian │ │Developer │
│  (Perm)  │      │  (Perm)  │ │  (Perm)  │ │(On-Dem)  │
│          │      │          │ │          │ │          │
│ Routes   │      │ Merges   │ │   Docs   │ │  Code    │
│ Reviews  │      │ to Main  │ │Generation│ │  Impl    │
└──────────┘      └──────────┘ └──────────┘ └──────────┘
       │                 │           │            │
       └─────────────────┴───────────┴────────────┘
                         │
                         ▼
          ┌─────────────────────────────────┐
          │   SQLite Database (Beads)        │
          │  • Features, Convoys, Tasks      │
          │  • Event Queue                   │
          │  • Agent Sessions                │
          │  • State Machine                 │
          └─────────────────────────────────┘
```

---

## Component Breakdown

### 1. CLI Layer (`ai_sprint/cli/`)

**Purpose**: User interface and command handling

**Commands:**
- `ai-sprint install` - Initialize system
- `ai-sprint health` - Check dependencies and system status
- `ai-sprint config` - Manage configuration
- `ai-sprint start <feature-dir>` - Start feature implementation
- `ai-sprint stop [--force]` - Stop running feature
- `ai-sprint status [--json] [--watch]` - View current status
- `ai-sprint logs <agent>` - View agent logs

**Technology**: Click framework for argument parsing and command routing

---

### 2. Core Agents (`ai_sprint/core/`)

#### Manager Agent (`manager.py`)

**Permanent**: Yes | **Count**: 1 | **Model**: Opus

**Responsibilities:**
- Poll database for ready features
- Parse `tasks.md` and create convoys
- Spawn Developer/Tester agents via tmux
- Monitor agent health (heartbeats, crashes)
- Restart failed agents automatically
- Detect feature completion and cleanup

**State Machine:**
```
Poll → Create Convoys → Spawn Agents → Monitor Health → Cleanup
   ↑                                                       ↓
   └───────────────────────────────────────────────────────┘
```

#### CAB Agent (`cab.py`)

**Permanent**: Yes | **Count**: 1 | **Model**: Haiku

**Responsibilities:**
- Route completed tasks from `InProgress` → `InReview`
- Run linting (ruff), type checking (mypy), complexity (radon)
- Approve → `InTests` or Reject → `InProgress` with feedback

**Quality Gates:**
- ✓ No linting errors (ruff)
- ✓ No type errors (mypy)
- ✓ Complexity ≤ 15 (radon)

#### Refinery Agent (`refinery.py`)

**Permanent**: Yes | **Count**: 1 | **Model**: Sonnet

**Responsibilities:**
- Route tasks from `InDocs` → merge
- Run security gates (semgrep, trivy, trufflehog)
- Execute sequential merges to main branch
- Handle merge conflicts (rebase strategy)

**Quality Gates:**
- ✓ No critical/high CVEs
- ✓ No secrets detected
- ✓ SAST findings acceptable

**Merge Strategy:**
```
1. Claim next task in merge queue
2. Rebase developer branch on main (handle conflicts)
3. Run security gates
4. Fast-forward merge to main
5. Cleanup worktree
6. Publish MERGE_TASK event
```

#### Librarian Agent (`librarian.py`)

**Permanent**: Yes | **Count**: 1 | **Model**: Sonnet

**Responsibilities:**
- Generate documentation after convoy completion
- Update README, API docs, architecture diagrams
- Triggered by UPDATE_DOCS event from Refinery

#### Developer Agent (`developer.py`)

**Permanent**: No | **Count**: 0-3 (configurable) | **Model**: Sonnet (default)

**Responsibilities:**
- Claim available convoy (atomic SQL transaction)
- Create git worktree for isolation
- Implement tasks sequentially within convoy
- Submit tasks to CAB for review
- Rework tasks on rejection
- Exit after convoy completion

**Lifecycle:**
```
Spawn → Claim Convoy → Create Worktree → Implement Tasks → Submit → Exit
                                   ↑                             ↓
                                   └─── Rejection (Rework) ──────┘
```

#### Tester Agent (`tester.py`)

**Permanent**: No | **Count**: 0-3 (configurable) | **Model**: Haiku

**Responsibilities:**
- Run test suites (pytest)
- Check coverage (pytest-cov, ≥80%)
- Run mutation tests (mutmut, ≥80%)
- Approve → `InDocs` or Reject → `InProgress`

---

### 3. State Management (`ai_sprint/services/state_manager.py`)

**Purpose**: SQLite-based state machine and event queue

**Key Operations:**
- Feature CRUD (create, read, update, delete)
- Convoy CRUD with file overlap validation
- Task CRUD with atomic claiming
- Event queue (publish, consume, acknowledge)
- State transitions with validation

**Database Schema:**

```sql
-- Features
CREATE TABLE features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_path TEXT NOT NULL,
    status TEXT CHECK (status IN ('ready', 'in_progress', 'done', 'failed')),
    created_at TEXT,
    started_at TEXT,
    completed_at TEXT
);

-- Convoys
CREATE TABLE convoys (
    id TEXT PRIMARY KEY,
    feature_id TEXT REFERENCES features(id),
    story TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT CHECK (status IN ('available', 'in_progress', 'done', 'blocked')),
    files TEXT,  -- JSON array
    dependencies TEXT,  -- JSON array
    assignee TEXT,
    created_at TEXT,
    started_at TEXT,
    completed_at TEXT
);

-- Tasks
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    convoy_id TEXT REFERENCES convoys(id),
    title TEXT NOT NULL,
    status TEXT CHECK (status IN ('todo', 'in_progress', 'in_review', 'in_tests', 'in_docs', 'done')),
    acceptance_criteria TEXT,  -- JSON array
    validation_results TEXT,  -- JSON object
    failure_reason TEXT,
    failure_count INTEGER DEFAULT 0,
    -- ... timestamps
);

-- Events (message queue)
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT,  -- JSON object
    status TEXT DEFAULT 'pending',
    created_at TEXT,
    processed_at TEXT
);

-- Agent Sessions
CREATE TABLE agent_sessions (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT,
    status TEXT CHECK (status IN ('active', 'crashed', 'hung', 'stuck')),
    last_heartbeat TEXT,
    -- ... convoy/task tracking
);
```

**Why SQLite?**
- ✓ ACID transactions (atomic convoy claiming)
- ✓ No external dependencies
- ✓ Built-in audit trail
- ✓ Survives process crashes
- ✓ Single-machine deployment

---

### 4. Session Management (`ai_sprint/services/session_manager.py`)

**Purpose**: tmux session lifecycle management

**Key Operations:**
- Create tmux session for feature
- Spawn agent in new pane
- Capture pane output to log file
- Kill session on feature completion

**Why tmux?**
- ✓ Session persistence (survives parent death)
- ✓ User inspection (`tmux attach -t ai-sprint-001`)
- ✓ Pane logging (automatic log capture)
- ✓ Standard tooling (widely available)

**Session Structure:**
```
tmux session: ai-sprint-001
├── pane-0: Manager agent
├── pane-1: CAB agent
├── pane-2: Refinery agent
├── pane-3: Librarian agent
├── pane-4: Developer-001 agent
├── pane-5: Developer-002 agent
└── pane-6: Tester-001 agent
```

---

### 5. Worktree Management (`ai_sprint/services/worktree_manager.py`)

**Purpose**: Git worktree isolation to prevent merge conflicts

**Key Operations:**
- Create worktree for convoy (`worktrees/convoy-us1/`)
- Create branch (`feature-001-convoy-us1`)
- Validate no file overlap between convoys
- Cleanup worktree on convoy completion

**Conflict Prevention:**
```python
# Before creating convoy, validate file overlap
convoy_files = ["src/auth.py", "src/user.py"]
existing_files = get_all_convoy_files(feature_id)

if any(f in existing_files for f in convoy_files):
    raise ConflictError("File overlap detected")
```

**Git Worktree Example:**
```
repo/                          (main branch)
├── worktrees/
│   ├── convoy-us1/           (branch: feature-001-convoy-us1)
│   │   └── src/auth.py       (isolated changes)
│   ├── convoy-us2/           (branch: feature-001-convoy-us2)
│   │   └── src/api.py        (different files, no conflict)
```

---

### 6. Quality Gates (`ai_sprint/services/quality_gates.py`)

**Purpose**: Multi-layer validation before merge

**Gate Stages:**

| Stage | Gates | Tools | Threshold |
|-------|-------|-------|-----------|
| InReview | Linting, Type Check, Complexity | ruff, mypy, radon | 0 errors, ≤15 cyclomatic |
| InTests | Coverage, Mutation | pytest-cov, mutmut | ≥80%, ≥80% |
| InDocs | SAST, CVE, Secrets | semgrep, trivy, trufflehog | 0 critical/high |

**Execution Flow:**
```
Developer submits → CAB runs linting/types/complexity
                    ↓ (pass)
              CAB approves → Tester runs coverage/mutation
                    ↓ (pass)
              Tester approves → Refinery runs SAST/CVE/secrets
                    ↓ (pass)
              Refinery merges to main
```

**Rejection Handling:**
- Generate specific feedback message
- Publish REWORK_NEEDED event to Developer
- Increment failure_count
- Escalate after 3 failures (future: Architect agent)

---

### 7. Health Monitoring (`ai_sprint/services/health_monitor.py`)

**Purpose**: Detect and recover from agent failures

**Detection Methods:**

| Failure Type | Detection | Threshold | Recovery |
|--------------|-----------|-----------|----------|
| Crash | Process not found | Immediate | Restart agent |
| Hung | No heartbeat | 5 minutes | Kill + restart |
| Stuck | Task timeout | 2 hours | Kill + restart, escalate task |

**Heartbeat Protocol:**
```python
# Every 60 seconds
agent.update_heartbeat()

# Health monitor checks
for session in active_sessions:
    if time_since_heartbeat(session) > 300:
        mark_hung(session)
        restart_agent(session)
```

---

## State Machine

### Task State Transitions

```
ToDo → InProgress → InReview → InTests → InDocs → Done
  ↑        ↓           ↓           ↓         ↓
  └────────┴───────────┴───────────┴─────────┘
       (Rejection with feedback)
```

**State Descriptions:**
- **ToDo**: Created, not claimed
- **InProgress**: Developer actively working
- **InReview**: CAB validating (linting, types, complexity)
- **InTests**: Tester validating (coverage, mutation)
- **InDocs**: Ready for merge (security gates run by Refinery)
- **Done**: Merged to main

**State Rules:**
- Only one transition per task at a time (atomic)
- Rejections reset to `InProgress` with `failure_reason`
- 3+ failures trigger escalation event

---

## Event-Driven Communication

### Event Types

| Event | Sender | Receiver | Payload | Purpose |
|-------|--------|----------|---------|---------|
| ROUTE_TASK | Developer/CAB | CAB/Tester | {task_id, from_state, to_state} | Route task to next stage |
| CLAIM_CONVOY | Developer | Manager | {convoy_id, agent_id} | Claim work |
| RUN_TESTS | CAB | Tester | {task_id} | Trigger test validation |
| SECURITY_SCAN | Tester | Refinery | {task_id} | Trigger security gates |
| MERGE_TASK | Refinery | Manager | {task_id, success} | Report merge completion |
| UPDATE_DOCS | Refinery | Librarian | {convoy_id} | Trigger documentation |
| REWORK_NEEDED | CAB/Tester/Refinery | Developer | {task_id, reason} | Rejection feedback |
| AGENT_CRASHED | Health Monitor | Manager | {agent_id, task_id} | Failure notification |

**Event Lifecycle:**
```
1. Agent publishes event (INSERT INTO events)
2. Target agent polls for pending events (SELECT WHERE agent_id = ? AND status = 'pending')
3. Agent claims event (UPDATE status = 'processing')
4. Agent processes event
5. Agent acknowledges event (UPDATE status = 'done')
```

---

## Convoy System

### Convoy Creation

```python
# From tasks.md
convoy = {
    "id": "convoy-us1",
    "story": "US1: End-to-end flow",
    "priority": "P1",
    "files": ["ai_sprint/core/manager.py", "ai_sprint/cli/commands/start.py"],
    "dependencies": [],  # No blockers
    "tasks": [
        {"id": "T027", "file_path": "ai_sprint/core/manager.py", ...},
        {"id": "T045", "file_path": "ai_sprint/cli/commands/start.py", ...},
    ]
}

# Validation
validate_no_file_overlap(convoy.files, existing_convoys)
create_convoy(convoy)
create_tasks(convoy.tasks)
```

### Convoy Allocation (FIFO)

```python
# Developer agent startup
convoy = claim_next_convoy(agent_id)  # Atomic SQL transaction

# Priority order
1. No dependencies (unblocked)
2. Highest priority (P1 > P2 > P3)
3. FIFO (oldest created_at)
```

### Convoy Completion

```python
# When all tasks done
if all_tasks_done(convoy_id):
    mark_convoy_complete(convoy_id)
    cleanup_worktree(convoy_id)
    unblock_dependent_convoys(convoy_id)
    check_feature_completion(feature_id)
```

---

## Quality Assurance Strategy

### Multi-Layer Defense

1. **Static Analysis (CAB)**
   - Linting (ruff): Style, imports, unused vars
   - Type checking (mypy): Type safety
   - Complexity (radon): Code maintainability

2. **Dynamic Testing (Tester)**
   - Coverage (pytest-cov): Exercise code paths
   - Mutation (mutmut): Test quality validation

3. **Security (Refinery)**
   - SAST (semgrep): Code vulnerabilities
   - CVE (trivy): Dependency vulnerabilities
   - Secrets (trufflehog): Leaked credentials

### Feedback Loop

```
Developer writes code
       ↓
CAB detects complexity violation (radon)
       ↓
Sends REWORK_NEEDED: "Function `process_data` has complexity 18 (max 15). Refactor."
       ↓
Developer refactors, resubmits
       ↓
CAB approves → InTests
```

---

## Failure Recovery

### Crash Recovery

```python
# Health monitor detects crash
if not process_exists(agent.pid):
    log.error(f"Agent {agent_id} crashed")

    # Release assigned convoy/task
    release_convoy(agent.convoy_id)

    # Restart agent
    new_agent = spawn_agent(agent_type)

    # Agent resumes from database state
    convoy = get_assigned_convoy(new_agent.id)
    if convoy:
        resume_work(convoy)
```

### Stuck Task Escalation

```python
# Task exceeds max duration
if task_duration(task) > config.task_max_duration:
    log.warning(f"Task {task.id} stuck after {duration}s")

    # Increment failure count
    task.failure_count += 1

    if task.failure_count >= 3:
        # Escalate to Architect (future feature)
        publish_event(ESCALATE_TASK, task_id=task.id)
    else:
        # Restart from scratch
        reset_task(task.id)
        release_convoy(task.convoy_id)
```

---

## Performance Characteristics

### Throughput

**Theoretical maximum** (with 3 developers, 3 testers):
- 3 convoys in parallel
- Average convoy: 5 tasks
- Average task: 30 minutes
- **Throughput**: ~3 convoys/hour = ~60 tasks/hour

**Real-world** (with quality gates, retries):
- ~2 convoys/hour = ~40 tasks/hour
- ~2-3 features per week (MVP complexity)

### Latency

| Operation | Latency | Bottleneck |
|-----------|---------|------------|
| Convoy claim | <100ms | SQLite atomic transaction |
| Task state transition | <100ms | SQLite UPDATE |
| Event publish/consume | <100ms | SQLite INSERT/SELECT |
| Agent heartbeat | <1s | tmux process check |
| Crash detection | <60s | Health monitor polling |

---

## Scalability Limits (MVP)

### Hard Limits

- **One feature at a time**: Serial feature execution
- **Single machine**: No distributed mode
- **3 developers max**: API rate limits, resource constraints
- **Sequential merging**: One merge at a time (conflict prevention)

### Future Improvements

- **Multi-feature support**: Queue multiple features
- **Distributed mode**: Run agents on different machines
- **Parallel merging**: Independent file changes
- **Agent pooling**: Reuse agent sessions across features

---

## Security Considerations

### Credential Management

- **API keys**: Via environment variables (not in config)
- **Git credentials**: SSH keys, not passwords
- **Database**: Local SQLite, no network exposure

### Isolation

- **Worktrees**: Separate working directories
- **tmux sessions**: Process isolation
- **Agent permissions**: Read-only main branch (until merge)

### Secrets Detection

- **Pre-merge scanning**: trufflehog on all changes
- **Rejection**: Any secrets detected → REWORK_NEEDED
- **Audit trail**: All rejections logged

---

## Observability

### Logging

**Levels:**
- `DEBUG`: All events, state transitions, agent actions
- `INFO`: Major events (convoy claimed, task completed)
- `WARNING`: Retries, timeouts
- `ERROR`: Crashes, failures

**Log Files:**
- `~/.ai-sprint/logs/ai-sprint.log` - Main application log
- `~/.ai-sprint/logs/manager.log` - Manager agent tmux pane
- `~/.ai-sprint/logs/developer-001.log` - Developer agent tmux pane
- etc.

### Monitoring

```bash
# Real-time status
ai-sprint status --watch

# View logs
ai-sprint logs manager --follow

# Attach to tmux session
tmux attach -t ai-sprint-001

# Database inspection
sqlite3 ~/.ai-sprint/beads.db "SELECT * FROM tasks WHERE status='in_progress'"
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|------------|---------|
| CLI | Click | Command-line interface |
| Agents | Claude API | AI-powered implementation |
| State | SQLite | Database and event queue |
| Logging | Rich | Terminal output formatting |
| Config | Pydantic + TOML | Settings management |
| Git | GitPython | Worktree and merge operations |
| Sessions | libtmux | Agent process management |
| Quality | ruff, mypy, radon, pytest, mutmut | Multi-layer validation |
| Security | semgrep, trivy, trufflehog | Vulnerability detection |

---

## Design Decisions

### Why SQLite over Redis?

✓ **SQLite:**
- ACID transactions (atomic convoy claiming)
- No external dependencies
- Built-in persistence
- SQL queries for complex filtering

✗ **Redis:**
- Requires external server
- Limited transaction support
- More complex deployment

### Why tmux over Direct Subprocess?

✓ **tmux:**
- Session persistence (survives parent death)
- User inspection capability
- Built-in logging
- Standard tooling

✗ **Direct subprocess:**
- No persistence
- Harder to debug
- Manual log management

### Why Worktrees over Branches?

✓ **Worktrees:**
- True filesystem isolation
- Prevent file conflicts
- Parallel development

✗ **Branches alone:**
- Shared working directory
- Merge conflicts possible
- Context switching overhead

---

## See Also

- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Quickstart Guide](quickstart.md)
- [Data Model](../specs/001-ai-sprint-system/data-model.md)
