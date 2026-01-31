# Data Model: AI Sprint System

**Branch**: `001-ai-sprint-system` | **Date**: 2026-01-25
**Source**: spec.md Key Entities section

---

## Entity Relationship Diagram

```
┌──────────────┐       ┌──────────────┐       ┌──────────────┐
│   Feature    │ 1───* │    Convoy    │ 1───* │     Task     │
├──────────────┤       ├──────────────┤       ├──────────────┤
│ id           │       │ id           │       │ id           │
│ name         │       │ feature_id   │───────│ convoy_id    │
│ spec_path    │       │ story        │       │ title        │
│ status       │       │ priority     │       │ description  │
│ created_at   │       │ status       │       │ file_path    │
│ started_at   │       │ files[]      │       │ status       │
│ completed_at │       │ dependencies │       │ priority     │
└──────────────┘       │ assignee     │       │ assignee     │
                       │ created_at   │       │ acceptance_  │
                       │ started_at   │       │   criteria[] │
                       │ completed_at │       │ validation_  │
                       └──────────────┘       │   results    │
                              │               │ created_at   │
                              │               │ started_at   │
                              │               │ completed_at │
                              │               └──────────────┘
                              │
                              │ 1
                              │
                              ▼ *
                       ┌──────────────┐
                       │ AgentSession │
                       ├──────────────┤
                       │ agent_id     │
                       │ agent_type   │
                       │ convoy_id    │
                       │ current_task │
                       │ worktree     │
                       │ status       │
                       │ last_heartbt │
                       │ started_at   │
                       │ crashed_at   │
                       └──────────────┘

┌──────────────┐
│    Event     │
├──────────────┤
│ id           │
│ agent_id     │
│ event_type   │
│ payload      │
│ status       │
│ created_at   │
│ processed_at │
└──────────────┘
```

---

## Entity Definitions

### Feature

**Purpose**: Top-level work unit representing a complete feature to implement

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, unique | UUID or slug (e.g., "001-ai-sprint-system") |
| name | string | required | Human-readable feature name |
| spec_path | string | required | Path to specs directory |
| status | enum | required | ready, in_progress, done, failed |
| created_at | datetime | required | When feature was registered |
| started_at | datetime | nullable | When implementation began |
| completed_at | datetime | nullable | When all convoys completed |

**Status Transitions**:
```
ready → in_progress (Manager creates convoys)
in_progress → done (All convoys complete)
in_progress → failed (Unrecoverable error)
```

**Validation Rules**:
- spec_path must contain spec.md, plan.md, tasks.md
- Only one feature can be in_progress at a time (MVP constraint)

---

### Convoy

**Purpose**: Bundle of related tasks (user story) assigned to single developer

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, unique | Format: convoy-{story-id} |
| feature_id | string | FK → Feature | Parent feature |
| story | string | required | User story name |
| priority | enum | required | P1, P2, P3, etc. |
| status | enum | required | available, in_progress, done, blocked |
| files | json array | required | List of file paths this convoy touches |
| dependencies | json array | nullable | List of convoy IDs that must complete first |
| assignee | string | nullable | Agent ID (dev-001, dev-002, etc.) |
| created_at | datetime | required | When convoy was created |
| started_at | datetime | nullable | When developer claimed convoy |
| completed_at | datetime | nullable | When all tasks done |

**Status Transitions**:
```
available → in_progress (Developer claims)
available → blocked (Dependencies not met)
blocked → available (Dependencies complete)
in_progress → done (All tasks complete)
```

**Validation Rules**:
- files array must not overlap with any other convoy in same feature
- dependencies must reference valid convoy IDs in same feature
- assignee must be valid agent_id when in_progress

**File Overlap Check**:
```sql
-- Validation query: find overlapping files
SELECT c1.id, c2.id, c1.files, c2.files
FROM convoys c1, convoys c2
WHERE c1.feature_id = c2.feature_id
  AND c1.id < c2.id
  AND json_array_length(
    json_extract(c1.files, '$')
  ) > 0
-- Additional intersection logic via Python
```

---

### Task

**Purpose**: Individual work item with acceptance criteria

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, unique | Format: T{number} |
| convoy_id | string | FK → Convoy | Parent convoy |
| title | string | required | Brief task description |
| description | string | required | Full task description |
| file_path | string | required | Primary file this task modifies |
| status | enum | required | todo, in_progress, in_review, in_tests, in_docs, done |
| priority | enum | required | P1, P2, P3 (inherited from convoy) |
| assignee | string | nullable | Agent ID handling this task |
| acceptance_criteria | json array | required | List of AC objects |
| validation_results | json object | nullable | Coverage, mutation, security results |
| failure_reason | string | nullable | Why task was rejected |
| failure_count | int | default: 0 | Number of times task failed |
| created_at | datetime | required | When task was created |
| started_at | datetime | nullable | When work began |
| completed_at | datetime | nullable | When task reached done |

**Status Transitions**:
```
todo → in_progress (Developer claims)
in_progress → in_review (Developer submits)
in_review → in_tests (CAB approves)
in_review → in_progress (CAB rejects)
in_tests → in_docs (Tester validates)
in_tests → in_progress (Tester rejects)
in_docs → done (Refinery merges)
in_docs → in_progress (Refinery rejects)
```

**Acceptance Criteria Structure**:
```json
{
  "acceptance_criteria": [
    {
      "id": "AC1",
      "description": "System creates convoy records from tasks.md",
      "satisfied": false,
      "validated_by": null,
      "validated_at": null
    }
  ]
}
```

**Validation Results Structure**:
```json
{
  "validation_results": {
    "coverage_percent": 85,
    "mutation_score": 82,
    "complexity_max": 8,
    "sast_findings": 0,
    "cve_critical": 0,
    "cve_high": 0,
    "secrets_found": 0,
    "validated_at": "2026-01-25T10:30:00Z"
  }
}
```

**Validation Rules**:
- file_path must be within convoy's files list
- acceptance_criteria must have at least one AC
- failure_count >= 3 triggers escalation

---

### Event

**Purpose**: Message queue for agent communication

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | PK, unique | UUID |
| agent_id | string | required | Target agent (cab, refinery, dev-001, etc.) |
| event_type | string | required | Event type code |
| payload | json object | required | Event-specific data |
| status | enum | required | pending, processing, done, failed |
| created_at | datetime | required | When event was created |
| processed_at | datetime | nullable | When agent processed event |

**Event Types**:

| Type | Sent By | Received By | Payload |
|------|---------|-------------|---------|
| ROUTE_TASK | Manager/Developer | CAB | {task_id, from_state, to_state} |
| CLAIM_CONVOY | Developer | Manager | {convoy_id, agent_id} |
| RUN_TESTS | CAB | Tester | {task_id} |
| SECURITY_SCAN | CAB | Refinery | {task_id} |
| MERGE_TASK | Refinery | Manager | {task_id, success} |
| UPDATE_DOCS | Refinery | Librarian | {convoy_id} |
| REWORK_NEEDED | CAB/Tester/Refinery | Developer | {task_id, reason} |
| AGENT_CRASHED | Manager | Manager | {agent_id, task_id} |
| ESCALATE_TASK | Manager | Architect | {task_id, failure_count} |

**Status Transitions**:
```
pending → processing (Agent picks up)
processing → done (Successfully handled)
processing → failed (Handler error)
```

---

### AgentSession

**Purpose**: Track active agent processes for health monitoring

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| agent_id | string | PK, unique | Format: {type}-{number} |
| agent_type | enum | required | manager, cab, refinery, librarian, developer, tester |
| convoy_id | string | FK → Convoy | Current convoy (workers only) |
| current_task | string | FK → Task | Task being worked on |
| worktree | string | nullable | Path to git worktree |
| status | enum | required | active, crashed, hung, stuck |
| last_heartbeat | datetime | required | Last health check |
| started_at | datetime | required | When session started |
| crashed_at | datetime | nullable | When crash detected |

**Status Transitions**:
```
active → crashed (Process terminated)
active → hung (No heartbeat for 5 min)
active → stuck (Task timeout)
crashed/hung/stuck → active (After restart)
```

**Agent Types and Counts**:

| Type | Permanent | Max Count |
|------|-----------|-----------|
| manager | Yes | 1 |
| cab | Yes | 1 |
| refinery | Yes | 1 |
| librarian | Yes | 1 |
| developer | No | 3 |
| tester | No | 3 |

---

## Database Schema (Raw SQL)

```sql
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Features table
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ready', 'in_progress', 'done', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Convoys table
CREATE TABLE IF NOT EXISTS convoys (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL REFERENCES features(id),
    story TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'in_progress', 'done', 'blocked')),
    files TEXT NOT NULL,  -- JSON array
    dependencies TEXT,     -- JSON array
    assignee TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    convoy_id TEXT NOT NULL REFERENCES convoys(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'in_review', 'in_tests', 'in_docs', 'done')),
    priority TEXT NOT NULL,
    assignee TEXT,
    acceptance_criteria TEXT NOT NULL,  -- JSON array
    validation_results TEXT,             -- JSON object
    failure_reason TEXT,
    failure_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Events table (message queue)
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,  -- JSON object
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT
);

-- Agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('manager', 'cab', 'refinery', 'librarian', 'developer', 'tester')),
    convoy_id TEXT REFERENCES convoys(id),
    current_task TEXT REFERENCES tasks(id),
    worktree TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'crashed', 'hung', 'stuck')),
    last_heartbeat TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    crashed_at TEXT
);
```

## Python Dataclasses

```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json

@dataclass
class Feature:
    id: str
    name: str
    spec_path: str
    status: str  # ready, in_progress, done, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Convoy:
    id: str
    feature_id: str
    story: str
    priority: str
    status: str  # available, in_progress, done, blocked
    files: list[str]
    created_at: datetime
    dependencies: list[str] = field(default_factory=list)
    assignee: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Task:
    id: str
    convoy_id: str
    title: str
    description: str
    file_path: str
    status: str  # todo, in_progress, in_review, in_tests, in_docs, done
    priority: str
    acceptance_criteria: list[dict]
    created_at: datetime
    assignee: Optional[str] = None
    validation_results: Optional[dict] = None
    failure_reason: Optional[str] = None
    failure_count: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

@dataclass
class Event:
    id: str
    agent_id: str
    event_type: str
    payload: dict
    created_at: datetime
    status: str = "pending"  # pending, processing, done, failed
    processed_at: Optional[datetime] = None

@dataclass
class AgentSession:
    agent_id: str
    agent_type: str  # manager, cab, refinery, librarian, developer, tester
    status: str  # active, crashed, hung, stuck
    last_heartbeat: datetime
    started_at: datetime
    convoy_id: Optional[str] = None
    current_task: Optional[str] = None
    worktree: Optional[str] = None
    crashed_at: Optional[datetime] = None
```

---

## Indexes

```sql
-- Event queue optimization
CREATE INDEX idx_events_agent_pending ON events(agent_id, status) WHERE status = 'pending';

-- Convoy allocation
CREATE INDEX idx_convoys_feature_status ON convoys(feature_id, status);
CREATE INDEX idx_convoys_assignee ON convoys(assignee);

-- Task tracking
CREATE INDEX idx_tasks_convoy ON tasks(convoy_id);
CREATE INDEX idx_tasks_status ON tasks(status);

-- Health monitoring
CREATE INDEX idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX idx_agent_sessions_heartbeat ON agent_sessions(last_heartbeat);
```

---

## Migration Notes

### Beads Compatibility

AI Sprint extends the existing Beads database. The following considerations apply:

1. **Existing tables preserved**: Beads' core tables remain unchanged
2. **New tables added**: features, convoys, agent_sessions, events
3. **Tasks table extended**: Add columns for acceptance_criteria, validation_results, etc.
4. **Schema versioning**: Simple version number in schema_version table

### Migration Pattern

```python
# ai_sprint/db/migrations.py

MIGRATIONS = {
    1: """
        CREATE TABLE IF NOT EXISTS features (...);
        CREATE TABLE IF NOT EXISTS convoys (...);
        CREATE TABLE IF NOT EXISTS events (...);
        CREATE TABLE IF NOT EXISTS agent_sessions (...);
    """,
    2: """
        ALTER TABLE tasks ADD COLUMN acceptance_criteria TEXT;
        ALTER TABLE tasks ADD COLUMN validation_results TEXT;
    """,
}

def get_current_version(conn) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except:
        return 0

def migrate(conn):
    current = get_current_version(conn)
    for version in sorted(MIGRATIONS.keys()):
        if version > current:
            conn.executescript(MIGRATIONS[version])
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
```
