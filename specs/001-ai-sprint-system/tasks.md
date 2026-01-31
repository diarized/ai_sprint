# Tasks: AI Sprint System

**Input**: Design documents from `/specs/001-ai-sprint-system/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-commands.md

**Tests**: Not explicitly requested - omitting test tasks per speckit:tasks protocol.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `ai_sprint/`, `tests/` at repository root (per plan.md structure)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per plan.md (ai_sprint/, tests/, scripts/, config/, docs/)
- [X] T002 Initialize Python project with pyproject.toml including Click, GitPython, libtmux, Pydantic, Rich dependencies
- [X] T003 [P] Create ai_sprint/__init__.py with package metadata
- [X] T004 [P] Create ai_sprint/__main__.py entry point for `python -m ai_sprint`
- [X] T005 [P] Configure ruff and mypy in pyproject.toml

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

### Data Models

- [X] T006 [P] Create Feature dataclass in ai_sprint/models/feature.py (status: ready/in_progress/done/failed)
- [X] T007 [P] Create Convoy dataclass in ai_sprint/models/convoy.py (status: available/in_progress/done/blocked)
- [X] T008 [P] Create Task dataclass in ai_sprint/models/task.py (status: todo/in_progress/in_review/in_tests/in_docs/done)
- [X] T009 [P] Create Event dataclass in ai_sprint/models/event.py (status: pending/processing/done/failed)
- [X] T010 [P] Create AgentSession dataclass in ai_sprint/models/agent_session.py (status: active/crashed/hung/stuck)
- [X] T011 Create ai_sprint/models/__init__.py exporting all models

### Database Layer

- [X] T012 Create database connection helper with WAL mode in ai_sprint/services/state_manager.py
- [X] T013 Implement schema creation (features, convoys, tasks, events, agent_sessions tables) in ai_sprint/services/state_manager.py
- [X] T014 Implement schema migration support (schema_version table) in ai_sprint/services/state_manager.py
- [X] T015 Create indexes for query optimization in ai_sprint/services/state_manager.py

### Configuration

- [X] T016 Create Pydantic Settings class in ai_sprint/config/settings.py (general, agents, timeouts, quality, security sections)
- [X] T017 [P] Create default thresholds in ai_sprint/config/defaults.py
- [X] T018 [P] Create example TOML config in config/ai-sprint.example.toml
- [X] T019 Create ai_sprint/config/__init__.py exporting Settings

### Utilities

- [X] T020 [P] Create Rich logging setup in ai_sprint/utils/logging.py
- [X] T021 [P] Create Git helpers (worktree operations) in ai_sprint/utils/git.py
- [X] T022 Create ai_sprint/utils/__init__.py

### CLI Framework

- [X] T023 Create Click CLI group in ai_sprint/cli/main.py
- [X] T024 Create CLI helpers in ai_sprint/cli/utils.py
- [X] T025 Create ai_sprint/cli/__init__.py
- [X] T026 Create ai_sprint/cli/commands/__init__.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Single Feature End-to-End (Priority: P1) - MVP

**Goal**: Autonomously implement all tasks from spec through merge with quality gates

**Independent Test**: Provide simple feature (3 tasks, 1 convoy), observe successful implementation through to merged code

### State Management Services

- [X] T027 [US1] Implement Feature CRUD operations in ai_sprint/services/state_manager.py
- [X] T028 [US1] Implement Convoy CRUD operations in ai_sprint/services/state_manager.py
- [X] T029 [US1] Implement Task CRUD operations with atomic claiming in ai_sprint/services/state_manager.py
- [X] T030 [US1] Implement Event queue operations (publish, consume, ack) in ai_sprint/services/state_manager.py

### Session Management

- [X] T031 [US1] Implement tmux session creation/destruction in ai_sprint/services/session_manager.py
- [X] T032 [US1] Implement agent spawning via tmux panes in ai_sprint/services/session_manager.py
- [X] T033 [US1] Implement session logging capture in ai_sprint/services/session_manager.py

### Core Agents

- [X] T034 [US1] Create Manager agent base (polling, convoy creation, agent spawning) in ai_sprint/core/manager.py
- [X] T035 [US1] Create CAB agent base (code review routing) in ai_sprint/core/cab.py
- [X] T036 [US1] Create Refinery agent base (merge operations) in ai_sprint/core/refinery.py
- [X] T037 [US1] Create Librarian agent base (documentation generation) in ai_sprint/core/librarian.py
- [X] T038 [US1] Create Developer agent base (task implementation) in ai_sprint/core/developer.py
- [X] T039 [US1] Create Tester agent base (validation execution) in ai_sprint/core/tester.py
- [X] T040 Create ai_sprint/core/__init__.py

### Task State Transitions

- [X] T041 [US1] Implement task state machine (todo->in_progress->in_review->in_tests->in_docs->done) in ai_sprint/services/state_manager.py
- [X] T042 [US1] Implement task rejection with failure reason in ai_sprint/services/state_manager.py
- [X] T043 [US1] Implement convoy completion detection in ai_sprint/services/state_manager.py
- [X] T044 [US1] Implement feature completion detection and cleanup in ai_sprint/services/state_manager.py

### CLI Commands (US1)

- [X] T045 [US1] Implement `ai-sprint start <feature-dir>` command in ai_sprint/cli/commands/start.py
- [X] T046 [US1] Implement feature validation (spec.md, plan.md, tasks.md existence) in ai_sprint/cli/commands/start.py
- [X] T047 [US1] Implement `ai-sprint stop [--force]` command in ai_sprint/cli/commands/stop.py
- [X] T048 [US1] Implement `ai-sprint status [--json] [--watch]` command in ai_sprint/cli/commands/status.py

**Checkpoint**: User Story 1 should be fully functional - single feature can complete end-to-end

---

## Phase 4: User Story 2 - Parallel Development with Conflict Prevention (Priority: P1)

**Goal**: Multiple agents work simultaneously without merge conflicts via worktree isolation

**Independent Test**: Create feature with 3 convoys touching different files, run 3 parallel developers, verify zero conflicts

### Worktree Management

- [X] T049 [US2] Implement worktree creation (one per developer) in ai_sprint/services/worktree_manager.py
- [X] T050 [US2] Implement worktree cleanup on convoy completion in ai_sprint/services/worktree_manager.py
- [X] T051 [US2] Implement branch management (unique branch per worktree) in ai_sprint/services/worktree_manager.py

### Conflict Prevention

- [X] T052 [US2] Implement file overlap validation between convoys in ai_sprint/services/state_manager.py
- [X] T053 [US2] Block feature start if file conflicts detected in ai_sprint/cli/commands/start.py
- [X] T054 [US2] Implement convoy file tracking in ai_sprint/services/state_manager.py

### Convoy Allocation

- [X] T055 [US2] Implement FIFO convoy allocation in ai_sprint/services/convoy_allocator.py
- [X] T056 [US2] Implement convoy dependency validation (block until dependencies complete) in ai_sprint/services/convoy_allocator.py
- [X] T057 [US2] Create ai_sprint/services/__init__.py exporting all services

### Sequential Merging

- [X] T058 [US2] Implement sequential merge queue in ai_sprint/core/refinery.py
- [X] T059 [US2] Implement fast-forward merge strategy in ai_sprint/core/refinery.py
- [X] T060 [US2] Implement rebase before merge (handle main branch changes) in ai_sprint/core/refinery.py

**Checkpoint**: User Stories 1 AND 2 should both work - parallel development without conflicts

---

## Phase 5: User Story 3 - Automatic Failure Recovery (Priority: P2)

**Goal**: Detect agent failures, restart automatically, resume work without data loss

**Independent Test**: Simulate agent crash (kill process), observe automatic restart and work resumption

### Health Monitoring

- [X] T061 [US3] Implement heartbeat mechanism in ai_sprint/services/health_monitor.py
- [X] T062 [US3] Implement crash detection (missing process) within 60 seconds in ai_sprint/services/health_monitor.py
- [X] T063 [US3] Implement hung agent detection (no heartbeat for 5 minutes) in ai_sprint/services/health_monitor.py
- [X] T064 [US3] Implement stuck task detection (exceeding duration limit) in ai_sprint/services/health_monitor.py

### Agent Recovery

- [X] T065 [US3] Implement automatic agent restart in ai_sprint/core/manager.py
- [X] T066 [US3] Implement state recovery after restart (read assigned task from DB) in ai_sprint/core/developer.py
- [X] T067 [US3] Implement failure count tracking (escalate after 3 failures) in ai_sprint/services/state_manager.py
- [X] T068 [US3] Implement task escalation event publishing in ai_sprint/services/state_manager.py

**Checkpoint**: User Story 3 complete - agents recover automatically from failures

---

## Phase 6: User Story 4 - Quality Gate Enforcement (Priority: P2)

**Goal**: All code passes quality gates before merge, failed code returned with specific feedback

**Independent Test**: Submit code failing each quality gate, verify rejection with specific feedback

### Quality Gate Framework

- [X] T069 [US4] Create quality gate runner framework in ai_sprint/services/quality_gates.py
- [X] T070 [US4] Implement linting gate (ruff integration) in ai_sprint/services/quality_gates.py
- [X] T071 [US4] Implement type checking gate (mypy integration) in ai_sprint/services/quality_gates.py
- [X] T072 [US4] Implement complexity gate (radon integration, max 15 cyclomatic) in ai_sprint/services/quality_gates.py

### Test Quality Gates

- [X] T073 [US4] Implement coverage gate (pytest-cov, min 80%) in ai_sprint/services/quality_gates.py
- [X] T074 [US4] Implement mutation testing gate (mutmut, min 80%) in ai_sprint/services/quality_gates.py

### Security Gates

- [X] T075 [US4] Implement SAST gate (semgrep integration) in ai_sprint/services/quality_gates.py
- [X] T076 [US4] Implement dependency scan gate (trivy integration) in ai_sprint/services/quality_gates.py
- [X] T077 [US4] Implement secret detection gate (trufflehog integration) in ai_sprint/services/quality_gates.py

### Gate Integration

- [X] T078 [US4] Integrate quality gates into CAB agent (InReview stage) in ai_sprint/core/cab.py
- [X] T079 [US4] Integrate test gates into Tester agent (InTests stage) in ai_sprint/core/tester.py
- [X] T080 [US4] Integrate security gates into Refinery agent (pre-merge) in ai_sprint/core/refinery.py
- [X] T081 [US4] Implement specific rejection messages per gate failure in ai_sprint/services/quality_gates.py

**Checkpoint**: User Story 4 complete - quality gates enforce code standards

---

## Phase 7: User Story 5 - GitHub Installation and Sharing (Priority: P3)

**Goal**: Easy installation on fresh machine with clear setup instructions and dependency validation

**Independent Test**: Clone to fresh VM/container, follow installation steps

### Installation Script

- [X] T082 [US5] Create system dependency checker script in scripts/install.sh
- [X] T083 [US5] Implement `ai-sprint install` command in ai_sprint/cli/commands/install.py
- [X] T084 [US5] Implement database initialization on first run in ai_sprint/cli/commands/install.py
- [X] T085 [US5] Implement config directory creation (~/.ai-sprint/) in ai_sprint/cli/commands/install.py

### Health Check

- [X] T086 [US5] Implement `ai-sprint health [--fix] [--json]` command in ai_sprint/cli/commands/health.py
- [X] T087 [US5] Implement dependency version checking in ai_sprint/cli/commands/health.py
- [X] T088 [US5] Implement optional tool detection (mutmut, semgrep, trivy) in ai_sprint/cli/commands/health.py

### Configuration Management

- [X] T089 [US5] Implement `ai-sprint config show` command in ai_sprint/cli/commands/config.py
- [X] T090 [US5] Implement `ai-sprint config set <key> <value>` command in ai_sprint/cli/commands/config.py
- [X] T091 [US5] Implement `ai-sprint config reset` command in ai_sprint/cli/commands/config.py

### Logging

- [X] T092 [US5] Implement `ai-sprint logs <agent>` command in ai_sprint/cli/commands/logs.py
- [X] T093 [US5] Implement log filtering (--tail, --follow, --since) in ai_sprint/cli/commands/logs.py

### Documentation

- [X] T094 [P] [US5] Create docs/installation.md
- [X] T095 [P] [US5] Create docs/configuration.md
- [X] T096 [P] [US5] Create docs/architecture.md

**Checkpoint**: User Story 5 complete - system installable from GitHub

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T097 [P] Create health-check.sh quick validation script in scripts/health-check.sh
- [ ] T098 [P] Add pyproject.toml entry points for `ai-sprint` command
- [ ] T099 Run quickstart.md validation (manual verification of all install/run steps)
- [ ] T100 Final code cleanup and docstring review

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - US1 (P1) and US2 (P1) can proceed in parallel after Foundational
  - US3 (P2) and US4 (P2) can proceed in parallel after Foundational
  - US5 (P3) can proceed after Foundational
- **Polish (Phase 8)**: Depends on all user story phases being complete

### User Story Dependencies

| Story | Priority | Depends On | Can Parallelize With |
|-------|----------|------------|---------------------|
| US1 | P1 | Foundational | US2 |
| US2 | P1 | Foundational | US1 |
| US3 | P2 | Foundational | US4 |
| US4 | P2 | Foundational | US3 |
| US5 | P3 | Foundational | US1, US2, US3, US4 |

### Within Each User Story

- Models before services
- Services before agents
- Core implementation before CLI integration
- Story complete before moving to next priority (unless parallelizing)

### Parallel Opportunities

**Phase 1 (Setup)**:
- T003, T004, T005 can run in parallel

**Phase 2 (Foundational)**:
- T006-T010 (models) can run in parallel
- T017, T018 can run in parallel
- T020, T021 can run in parallel

**Phase 3-7 (User Stories)**:
- US1 and US2 (both P1) can run in parallel with different developers
- US3 and US4 (both P2) can run in parallel with different developers
- Within each story, tasks marked [P] can run in parallel

**Phase 8 (Polish)**:
- T094, T095, T096 documentation tasks can run in parallel
- T097, T098 can run in parallel

---

## Parallel Example: Foundational Phase Models

```bash
# Launch all model creation tasks together:
Task: "Create Feature dataclass in ai_sprint/models/feature.py"
Task: "Create Convoy dataclass in ai_sprint/models/convoy.py"
Task: "Create Task dataclass in ai_sprint/models/task.py"
Task: "Create Event dataclass in ai_sprint/models/event.py"
Task: "Create AgentSession dataclass in ai_sprint/models/agent_session.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (end-to-end flow)
4. Complete Phase 4: User Story 2 (parallel development)
5. **STOP and VALIDATE**: Test both stories independently
6. Deploy/demo if ready - core value delivered

### Incremental Delivery

| Milestone | Phases | Value Delivered |
|-----------|--------|-----------------|
| Foundation | 1, 2 | Core infrastructure ready |
| MVP | 3, 4 | End-to-end feature automation with parallel execution |
| Robust | 5, 6 | Automatic recovery and quality enforcement |
| Shareable | 7, 8 | Easy installation and documentation |

### Convoy Mapping for AI Sprint

| Convoy | User Story | Tasks | File Scope |
|--------|------------|-------|------------|
| convoy-setup | Setup | T001-T005 | project root, ai_sprint/__init__.py, pyproject.toml |
| convoy-foundation | Foundational | T006-T026 | ai_sprint/models/, ai_sprint/config/, ai_sprint/utils/, ai_sprint/cli/ (base) |
| convoy-us1 | US1 | T027-T048 | ai_sprint/services/state_manager.py, ai_sprint/services/session_manager.py, ai_sprint/core/, ai_sprint/cli/commands/start.py, stop.py, status.py |
| convoy-us2 | US2 | T049-T060 | ai_sprint/services/worktree_manager.py, ai_sprint/services/convoy_allocator.py |
| convoy-us3 | US3 | T061-T068 | ai_sprint/services/health_monitor.py |
| convoy-us4 | US4 | T069-T081 | ai_sprint/services/quality_gates.py |
| convoy-us5 | US5 | T082-T096 | scripts/, ai_sprint/cli/commands/install.py, health.py, config.py, logs.py, docs/ |
| convoy-polish | Polish | T097-T100 | scripts/, pyproject.toml |

---

## Notes

- [P] tasks = different files, no dependencies within phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- US1+US2 (both P1) represent MVP - core value proposition
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
