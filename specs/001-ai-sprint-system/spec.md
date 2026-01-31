# Feature Specification: AI Sprint System

**Feature Branch**: `001-ai-sprint-system`
**Created**: 2026-01-25
**Status**: Draft
**Input**: Multi-agent orchestration system for autonomous software development from specification to deployment

---

## Overview

AI Sprint is a multi-agent orchestration system that enables autonomous software development. The system coordinates multiple AI agents to implement features from specification through to merged, tested, documented code - without human intervention during the development cycle.

**Core Value Proposition**: Transform feature specifications into production-ready code through coordinated AI agents with built-in quality gates, automatic failure recovery, and guaranteed conflict-free merging.

**Design Philosophy**: Operational roles (Gas Town "Mayor" pattern) over SDLC personas. Agents are orchestrators, workers, and validators - not "Product Managers" or "Developers" role-playing.

---

## User Scenarios & Testing

### User Story 1 - Single Feature End-to-End (Priority: P1)

A user has a feature specification (spec.md), implementation plan (plan.md), and task list (tasks.md) ready. They want the system to autonomously implement all tasks, run quality checks, merge code, and generate documentation.

**Why this priority**: This is the core value proposition. Without end-to-end automation, the system provides no value over manual development.

**Independent Test**: Can be fully tested by providing a simple feature (3 tasks, 1 convoy) and observing successful implementation through to merged code with passing tests.

**Acceptance Scenarios**:

1. **Given** spec.md + plan.md + tasks.md exist for a feature, **When** user starts AI Sprint, **Then** system creates convoys from tasks and spawns worker agents
2. **Given** worker agents are active, **When** a developer agent completes a task, **Then** the task transitions through quality gates (review → tests → security → merge)
3. **Given** all tasks in a convoy are done, **When** convoy completes, **Then** documentation is automatically generated
4. **Given** all convoys for a feature are done, **When** feature completes, **Then** user is notified and temporary resources are cleaned up
5. **Given** a quality gate fails (coverage < 80%, security issue found), **When** task is rejected, **Then** task returns to development with specific failure reason

---

### User Story 2 - Parallel Development with Conflict Prevention (Priority: P1)

A user has a feature with multiple user stories that can be developed in parallel. They want multiple agents to work simultaneously without creating merge conflicts.

**Why this priority**: Parallelism is essential for throughput. Without conflict prevention, the system cannot operate autonomously (human intervention required for merge conflicts).

**Independent Test**: Can be tested by creating a feature with 3 convoys touching different files, running 3 parallel developers, and verifying zero merge conflicts.

**Acceptance Scenarios**:

1. **Given** tasks.md defines file paths for each task, **When** convoys are created, **Then** system validates no file overlap between convoys
2. **Given** file overlap is detected between convoys, **When** validation runs, **Then** system blocks feature start and reports conflicting files
3. **Given** 3 developers are working in parallel, **When** each claims a convoy, **Then** each works in an isolated git worktree
4. **Given** convoy-A depends on convoy-B, **When** developer requests work, **Then** convoy-A is not available until convoy-B completes
5. **Given** developers finish in different order, **When** merging, **Then** merges happen sequentially with no conflicts

---

### User Story 3 - Automatic Failure Recovery (Priority: P2)

An agent crashes or becomes unresponsive during work. The system automatically detects the failure, restarts the agent, and resumes work without losing progress.

**Why this priority**: Critical for autonomous operation. If crashes require human intervention, the system cannot run unattended.

**Independent Test**: Can be tested by simulating agent crash (kill process) and observing automatic restart and work resumption.

**Acceptance Scenarios**:

1. **Given** an agent is working on a task, **When** the agent process terminates unexpectedly, **Then** system detects within 60 seconds
2. **Given** crash is detected, **When** system restarts agent, **Then** agent reads its assigned task from state store and resumes
3. **Given** an agent stops sending heartbeats for 5 minutes, **When** timeout triggers, **Then** system kills and restarts the agent
4. **Given** a task exceeds 2 hours duration, **When** timeout triggers, **Then** task is marked failed and escalated
5. **Given** a task fails 3 times, **When** third failure occurs, **Then** task is blocked and escalated for human review

---

### User Story 4 - Quality Gate Enforcement (Priority: P2)

All code must pass quality gates before merging: test coverage, mutation testing, complexity limits, and security scans. Failed code is automatically returned for fixes.

**Why this priority**: Quality gates are the mechanism that makes autonomous development trustworthy. Without enforcement, the system produces unreliable code.

**Independent Test**: Can be tested by submitting code that fails each quality gate and verifying rejection with specific feedback.

**Acceptance Scenarios**:

1. **Given** code with 65% test coverage, **When** test quality check runs, **Then** task is rejected with message "Coverage 65% < 80%"
2. **Given** code with mutation score 70%, **When** mutation testing runs, **Then** task is rejected with message "Mutation score 70% < 80%"
3. **Given** code with cyclomatic complexity 18, **When** complexity check runs, **Then** task is rejected with message "Complexity 18 > 15"
4. **Given** code with critical CVE in dependency, **When** security scan runs, **Then** merge is blocked with CVE details
5. **Given** code with hardcoded secret, **When** secret detection runs, **Then** merge is blocked with secret location
6. **Given** all quality gates pass, **When** merge attempt runs, **Then** code is merged to main and regression tests execute

---

### User Story 5 - GitHub Installation and Sharing (Priority: P3)

A new user clones the repository and installs the system on a fresh machine. The system provides clear setup instructions and validates dependencies.

**Why this priority**: Enables adoption and contribution. Without easy installation, the system remains a single-user tool.

**Independent Test**: Can be tested by cloning to a fresh VM/container and following installation steps.

**Acceptance Scenarios**:

1. **Given** user clones repository, **When** they run installation script, **Then** all dependencies are checked and installed
2. **Given** a dependency is missing, **When** install runs, **Then** clear error message explains what to install
3. **Given** Beads is not configured, **When** install runs, **Then** system creates required schema extensions
4. **Given** installation completes, **When** user runs health check, **Then** all components report ready status
5. **Given** user wants to configure thresholds, **When** they edit config file, **Then** system uses new thresholds on next run

---

### Edge Cases

- What happens when the main branch changes during development? (Refinery rebases before merge)
- How does system handle network/API failures to AI providers? (Retry with exponential backoff, escalate after 3 failures)
- What happens if Beads database becomes corrupted? (System fails gracefully, requires manual recovery)
- How does system handle tasks that reference non-existent files? (Validation at convoy creation, block if files don't exist in plan)
- What happens if two features are started simultaneously? (Features queue, one runs at a time for MVP)

---

## Requirements

### Functional Requirements - Core Orchestration

- **FR-001**: System MUST read feature specifications from spec.md, plan.md, and tasks.md files
- **FR-002**: System MUST create convoy records from tasks.md, grouping tasks by user story
- **FR-003**: System MUST spawn worker agents in isolated execution environments
- **FR-004**: System MUST route tasks through states: ToDo → InProgress → InReview → InTests → InDocs → Done
- **FR-005**: System MUST detect convoy completion when all convoy tasks reach Done state
- **FR-006**: System MUST detect feature completion when all feature convoys reach Done state
- **FR-007**: System MUST clean up temporary resources (worktrees, sessions) after feature completion

### Functional Requirements - Parallel Development

- **FR-008**: System MUST validate no file overlap between convoys before starting feature
- **FR-009**: System MUST create isolated git worktrees for each active developer agent
- **FR-010**: System MUST enforce FIFO convoy allocation (first created, first claimed)
- **FR-011**: System MUST block convoy assignment when dependencies are unmet
- **FR-012**: System MUST track file paths per convoy to prevent concurrent modification
- **FR-013**: System MUST merge completed work sequentially (one merge at a time)
- **FR-014**: System MUST use fast-forward merges to maintain linear history

### Functional Requirements - Quality Gates

- **FR-015**: System MUST run automated code review (linting, type checking, complexity analysis) at InReview stage
- **FR-016**: System MUST run test quality validation (coverage, mutation score, AC traceability) at InTests stage
- **FR-017**: System MUST run security validation (SAST, dependency scan, secret detection) before merge
- **FR-018**: System MUST run regression tests after merge and revert on failure
- **FR-019**: System MUST return failed tasks to InProgress with specific failure reason
- **FR-020**: System MUST enforce configurable thresholds (default: 80% coverage, 80% mutation, ≤15 complexity)
- **FR-021**: System MUST block merge for critical/high CVEs and detected secrets (zero tolerance)

### Functional Requirements - Failure Recovery

- **FR-022**: System MUST monitor agent health via heartbeat mechanism
- **FR-023**: System MUST detect agent crashes (missing process) within 60 seconds
- **FR-024**: System MUST detect hung agents (no heartbeat) within 5 minutes
- **FR-025**: System MUST detect stuck tasks (exceeding duration limit) within configured timeout
- **FR-026**: System MUST automatically restart crashed/hung agents
- **FR-027**: System MUST preserve task state in persistent storage for recovery
- **FR-028**: System MUST escalate tasks after configurable failure count (default: 3)

### Functional Requirements - State Management

- **FR-029**: System MUST store task state, convoy state, and agent state in persistent storage
- **FR-030**: System MUST support atomic task claiming (prevent race conditions)
- **FR-031**: System MUST maintain event queue for agent communication
- **FR-032**: System MUST store acceptance criteria per task for validation
- **FR-033**: System MUST track validation results (coverage %, mutation %, security findings)

### Functional Requirements - Documentation

- **FR-034**: System MUST generate As-Built documentation when convoy completes
- **FR-035**: System MUST update documentation index when feature completes
- **FR-036**: System MUST log all state transitions and quality gate results

### Functional Requirements - Installation

- **FR-037**: System MUST provide installation script that validates dependencies
- **FR-038**: System MUST provide configuration file for customizable thresholds
- **FR-039**: System MUST provide health check command to verify installation
- **FR-040**: System MUST initialize database schema on first run
- **FR-041**: System MUST provide clear error messages for missing dependencies

### Key Entities

- **Feature**: Top-level work unit, contains convoys, has status (ready/in-progress/done)
- **Convoy**: Bundle of related tasks (user story), assigned to one developer, has file list and dependencies
- **Task**: Individual work item with acceptance criteria, file path, status, and validation results
- **Event**: Message in agent communication queue, has type, payload, and processing status
- **Agent Session**: Record of active agent, tracks assigned work, heartbeat, and worktree location

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: A feature with 3 convoys and 15 tasks completes successfully without human intervention
- **SC-002**: System supports 3 parallel developer agents working on different convoys simultaneously
- **SC-003**: Zero merge conflicts occur when convoys touch different files (file isolation validated)
- **SC-004**: Quality gates correctly reject code failing thresholds in 100% of test cases
- **SC-005**: Crashed agents are detected and restarted within 2 minutes
- **SC-006**: Restarted agents resume their assigned work without data loss
- **SC-007**: Task failure reasons are specific and actionable (not generic error messages)
- **SC-008**: New user can install system on fresh machine following documentation in under 30 minutes
- **SC-009**: System runs for 8+ hours unattended without requiring human intervention
- **SC-010**: All state transitions are logged and queryable for debugging

---

## Constraints & Assumptions

### Constraints (from locked specifications)

- Maximum 10 concurrent agents (4 infrastructure + 3 developers + 3 testers at peak)
- Sequential merge strategy (one merge at a time to main branch)
- File isolation enforced at planning phase (architect/scrum master responsibility)
- Quality thresholds: 80% coverage, 80% mutation, ≤15 complexity, zero critical/high CVEs
- Agent models: Haiku for high-frequency/low-complexity, Sonnet for medium complexity, Opus for rare/high-complexity

### Assumptions

- Beads (SQLite-based state management) is available and functional
- Git is available with worktree support
- tmux is available for session management
- AI provider API (Claude) is accessible
- Target project has testing framework configured
- Security scanning tools (Semgrep, Trivy, TruffleHog) are available or installable

### Out of Scope (MVP)

- Multiple simultaneous features (queue and process one at a time)
- DAST (Dynamic Application Security Testing)
- Custom AI provider support (Claude only for MVP)
- Web UI for monitoring (CLI and logs only)
- Distributed operation (single machine only)

---

## References

- Main Specification: `artifacts/AI_SPRINT_SPECIFICATION_v1.0.md`
- Infrastructure Decisions: `artifacts/topic1_infrastructure_LOCKED.md`
- Quality Gate Decisions: `artifacts/topic2_quality_gates_LOCKED.md`
- Coordination Decisions: `artifacts/topic3_coordination_LOCKED.md`
- Gas Town Architecture: https://github.com/steveyegge/gastown
