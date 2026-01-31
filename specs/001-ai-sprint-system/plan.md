# Implementation Plan: AI Sprint System

**Branch**: `001-ai-sprint-system` | **Date**: 2026-01-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ai-sprint-system/spec.md`

---

## Summary

AI Sprint is a multi-agent orchestration system that autonomously implements software features from specification to deployment. The system coordinates 9 agent types (4 permanent infrastructure + 5 on-demand workers) using Git worktree isolation, SQLite-based state management (Beads), and quality gates to produce reliable, tested, documented code without human intervention.

**Technical Approach**: Python 3.11+ CLI application with SQLite persistence, tmux session management, and subprocess-based agent spawning. Designed for GitHub distribution with pip/pipx installation.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**:
- Click (CLI framework)
- GitPython (worktree management)
- libtmux (tmux session control)
- Pydantic (configuration and validation)
- Rich (terminal output and logging)
- sqlite3 (standard library - no ORM)

**Storage**: SQLite (Beads database, extended schema for events/convoys/tasks)

**Testing**: pytest with pytest-cov, pytest-mock

**Target Platform**: Linux (primary), macOS (secondary)

**Project Type**: Single CLI application

**Performance Goals**:
- Agent health check latency <1s
- State transition latency <100ms
- Support 10 concurrent agents without resource exhaustion

**Constraints**:
- Single machine operation (no distributed mode for MVP)
- One feature at a time (queue multiple features)
- Sequential merging (one merge operation at a time)

**Scale/Scope**:
- 10 concurrent agents maximum
- ~1.3M tokens per feature
- 2-3 features per week target throughput

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Design Validation

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | PASS | spec.md created before plan.md; spec is technology-agnostic |
| II. Technology-Agnostic Spec | PASS | spec.md describes WHAT (orchestration, quality gates), not HOW (Python, SQLite) |
| III. Template-Based Consistency | PASS | Using standard spec-template.md and plan-template.md |
| IV. Iterative Refinement | PASS | Checklist validated in `checklists/requirements.md` |
| V. User Story Independence | PASS | 5 user stories, each independently testable, P1 = MVP |
| VI. Research-Driven Decisions | IN PROGRESS | research.md to be created in Phase 0 |

### Post-Design Validation (after Phase 1)

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Specification-First | PASS | Plan derived from spec requirements |
| II. Technology-Agnostic Spec | PASS | Tech choices documented in plan only |
| III. Template-Based Consistency | PASS | All required artifacts generated |
| IV. Iterative Refinement | PASS | Research completed, clarifications resolved |
| V. User Story Independence | PASS | Tasks will be grouped by user story in tasks.md |
| VI. Research-Driven Decisions | PASS | research.md documents technology rationale |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-ai-sprint-system/
├── spec.md              # Feature specification (created)
├── plan.md              # This file
├── research.md          # Phase 0: Technology decisions
├── data-model.md        # Phase 1: Entity schemas
├── quickstart.md        # Phase 1: Installation and usage guide
├── contracts/           # Phase 1: CLI interface definitions
│   └── cli-commands.md  # Command specifications
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (created)
└── tasks.md             # Phase 2: Implementation tasks (/speckit:tasks)
```

### Source Code (repository root)

```text
ai_sprint/
├── __init__.py              # Package metadata
├── __main__.py              # Entry point (python -m ai_sprint)
├── cli/
│   ├── __init__.py
│   ├── main.py              # Click CLI group
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── start.py         # ai-sprint start <feature>
│   │   ├── status.py        # ai-sprint status
│   │   ├── stop.py          # ai-sprint stop
│   │   ├── health.py        # ai-sprint health
│   │   └── install.py       # ai-sprint install
│   └── utils.py             # CLI helpers
├── core/
│   ├── __init__.py
│   ├── manager.py           # Manager agent (orchestrator)
│   ├── cab.py               # CAB agent (router)
│   ├── refinery.py          # Refinery agent (merger)
│   ├── librarian.py         # Librarian agent (documentation)
│   ├── developer.py         # Developer agent (implementation)
│   └── tester.py            # Tester agent (validation)
├── models/
│   ├── __init__.py
│   ├── feature.py           # Feature entity
│   ├── convoy.py            # Convoy entity
│   ├── task.py              # Task entity with AC
│   ├── event.py             # Event queue entity
│   └── agent_session.py     # Agent session tracking
├── services/
│   ├── __init__.py
│   ├── state_manager.py     # Beads/SQLite operations
│   ├── worktree_manager.py  # Git worktree operations
│   ├── session_manager.py   # tmux session operations
│   ├── quality_gates.py     # Validation runners
│   ├── health_monitor.py    # Agent health watchdog
│   └── convoy_allocator.py  # FIFO convoy distribution
├── config/
│   ├── __init__.py
│   ├── settings.py          # Pydantic settings
│   └── defaults.py          # Default thresholds
└── utils/
    ├── __init__.py
    ├── logging.py           # Rich logging setup
    └── git.py               # GitPython helpers

tests/
├── conftest.py              # pytest fixtures
├── unit/
│   ├── test_models.py
│   ├── test_state_manager.py
│   ├── test_convoy_allocator.py
│   └── test_quality_gates.py
├── integration/
│   ├── test_manager_flow.py
│   ├── test_worktree_lifecycle.py
│   └── test_session_lifecycle.py
└── e2e/
    └── test_full_feature.py

scripts/
├── install.sh               # System dependency installer
└── health-check.sh          # Quick validation script

config/
├── ai-sprint.toml           # User configuration (thresholds, models)
└── ai-sprint.example.toml   # Example configuration

docs/
├── installation.md
├── quickstart.md            # Copied to specs/ for feature context
├── configuration.md
└── architecture.md
```

**Structure Decision**: Single CLI project structure chosen. The system is a standalone tool, not a web application or mobile app. All components run in a single process with subprocess spawning for agents.

---

## Complexity Tracking

> No constitution violations. Complexity is inherent to the multi-agent orchestration domain.

| Aspect | Justification | Simpler Alternative Considered |
|--------|---------------|-------------------------------|
| 9 agent types | Required by specification (4 infrastructure + 5 on-demand) | Single agent rejected: cannot parallelize, no role separation |
| SQLite (raw) | Atomic operations, audit trail, recovery | File-based rejected: race conditions, no transactions |
| tmux sessions | Process isolation, session persistence, user inspection | Direct subprocess rejected: no persistence, harder debugging |

---

## Component Architecture

### Agent Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Sprint CLI                            │
│  ai-sprint start <feature-dir>                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Manager (Permanent)                         │
│  - Polls for ready features                                 │
│  - Creates convoys from tasks.md                            │
│  - Spawns Developer/Tester agents                           │
│  - Monitors health, restarts crashed agents                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ Events via SQLite queue
          ┌───────────┼───────────┬───────────┐
          ▼           ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
     │   CAB   │ │Refinery │ │Librarian│ │Developer│
     │ (Perm)  │ │ (Perm)  │ │ (Perm)  │ │(On-Dem) │
     └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### State Transitions

```
Task: ToDo → InProgress → InReview → InTests → InDocs → Done
              │            │          │         │
              │            │          │         └─ Refinery merge fails
              │            │          └─ Tester validation fails
              │            └─ CAB code review fails
              └─ Developer claims task
```

### Quality Gates

| Stage | Gate | Tools | Threshold |
|-------|------|-------|-----------|
| InReview | Linting | ruff, mypy | Zero errors |
| InReview | Complexity | radon | ≤15 cyclomatic |
| InTests | Coverage | pytest-cov | ≥80% |
| InTests | Mutation | mutmut | ≥80% |
| InDocs | Security | semgrep, trivy, trufflehog | Zero critical/high |

---

## External Dependencies

### System Requirements

| Dependency | Version | Purpose | Required |
|------------|---------|---------|----------|
| Python | 3.11+ | Runtime | Yes |
| Git | 2.20+ | Worktree support | Yes |
| tmux | 3.0+ | Session management | Yes |
| SQLite | 3.35+ | Database | Yes (bundled) |

### Python Packages

| Package | Version | Purpose |
|---------|---------|---------|
| click | ^8.0 | CLI framework |
| gitpython | ^3.1 | Git operations |
| libtmux | ^0.37 | tmux control |
| pydantic | ^2.0 | Configuration |
| pydantic-settings | ^2.0 | Environment config |
| rich | ^13.0 | Terminal output |
| toml | ^0.10 | Config parsing |

### Security Tools (Optional, installed separately)

| Tool | Purpose | Installation |
|------|---------|--------------|
| semgrep | SAST scanning | pip install semgrep |
| trivy | CVE scanning | brew/apt install trivy |
| trufflehog | Secret detection | pip install trufflehog |
| ruff | Linting | pip install ruff |
| mypy | Type checking | pip install mypy |
| mutmut | Mutation testing | pip install mutmut |

---

## Configuration Schema

```toml
# ai-sprint.toml

[general]
database_path = "~/.ai-sprint/beads.db"
log_level = "INFO"
log_file = "~/.ai-sprint/logs/ai-sprint.log"

[agents]
max_developers = 3
max_testers = 3
polling_interval_seconds = 30

[timeouts]
agent_heartbeat_seconds = 60
agent_hung_seconds = 300
task_max_duration_seconds = 7200
merge_timeout_seconds = 300

[quality]
coverage_threshold = 80
mutation_threshold = 80
complexity_flag = 10
complexity_max = 15

[security]
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 5

[models]
manager = "haiku"
cab = "haiku"
refinery = "sonnet"
librarian = "sonnet"
developer = "sonnet"
tester = "haiku"
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| tmux not available | Low | High | Validate at install, provide docker alternative |
| Beads schema conflicts | Medium | Medium | Version schema, migration support |
| Agent API rate limits | Medium | High | Exponential backoff, configurable limits |
| Merge conflicts despite isolation | Low | High | Strict file overlap validation at convoy creation |
| Long-running tasks timeout | Medium | Medium | Configurable timeouts, task checkpointing |

---

## Implementation Notes

### Why Python over Bash

The original specification used Bash pseudocode. Python chosen for:
1. **Robustness**: Exception handling, type hints, testing
2. **Maintainability**: Dataclasses + helper functions, structured logging
3. **Distribution**: pip/pipx installation vs script copying
4. **Error handling**: Graceful degradation, meaningful errors

### Why SQLite over Files

1. **Atomicity**: SQL transactions prevent race conditions in claiming
2. **Queryability**: Complex queries for convoy allocation, health checks
3. **Audit trail**: Built-in history for debugging
4. **Recovery**: Database state survives crashes

### Why tmux over Direct Subprocess

1. **Persistence**: Sessions survive parent process death
2. **Inspection**: User can attach to see agent activity
3. **Management**: Standard tooling for session control
4. **Logging**: Built-in pane logging support
