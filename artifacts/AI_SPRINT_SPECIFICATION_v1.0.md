# AI Sprint System - Complete Specification v1.0

**Date**: 2026-01-25
**Status**: Ready for Implementation
**Purpose**: Bullet-proof specification (WHAT and WHY) with constraints (HOW) for multi-agent AI software development system

---

## Executive Summary

**AI Sprint** is a multi-agent orchestration system that produces highly reliable software from specification to deployment using:

- **9 agent types** with clear operational roles (Mayor pattern, not SDLC personas)
- **4 permanent infrastructure agents** + up to 6 on-demand workers (peak: 10 concurrent)
- **Git worktree isolation** for parallel development without merge conflicts
- **Beads-based state management** for atomic task claiming and event queuing
- **Automated quality gates** (80% coverage, 80% mutation, ≤15 complexity, zero critical CVEs)
- **Sequential merge strategy** for stable main branch
- **Automatic failure recovery** with health monitoring and escalation

**Estimated Throughput:** 2-3 features/week initially, scaling to 5-7 with optimization

**Token Budget:** ~960k per feature + 60M/week infrastructure overhead

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Agent Roles & Responsibilities](#agent-roles--responsibilities)
3. [Infrastructure Components](#infrastructure-components)
4. [Quality Gates & Validation](#quality-gates--validation)
5. [Coordination & Recovery](#coordination--recovery)
6. [Complete Task Flow](#complete-task-flow)
7. [Token Budget & Throughput](#token-budget--throughput)
8. [Implementation Roadmap](#implementation-roadmap)
9. [References](#references)

---

## Architecture Overview

### Design Philosophy

**Operational Roles (Gas Town Pattern)** instead of SDLC Personas (BMAD Pattern):
- **NOT**: "Product Manager" → "Architect" → "Developer"
- **YES**: "Manager (Mayor)" → "Workers (Polecats)" → "Refinery (Merger)"

**Benefits:**
- Clearer responsibilities (orchestration vs execution)
- Better parallelism (workers don't hand off sequentially)
- Proven at scale (Gas Town: 20-30 agents)

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI SPRINT SYSTEM                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐     ┌──────────────────────────────────┐      │
│  │   Manager   │────▶│        Beads Event Queue         │      │
│  │  (Haiku)    │     │      (SQLite-based)              │      │
│  │  Permanent  │     └──────────────────────────────────┘      │
│  └─────────────┘              │         │         │             │
│        │                      │         │         │             │
│        │                      ▼         ▼         ▼             │
│  ┌─────▼─────┐         ┌─────────┐ ┌─────────┐ ┌──────────┐   │
│  │    CAB    │         │Refinery │ │Librarian│ │Developer │   │
│  │  (Haiku)  │         │(Sonnet) │ │(Sonnet) │ │(Sonnet)  │   │
│  │ Permanent │         │Permanent│ │Permanent│ │On-Demand │   │
│  └───────────┘         └─────────┘ └─────────┘ └──────────┘   │
│        │                     │           │           │          │
│        │                     │           │           │          │
│  ┌─────▼────────────────────▼───────────▼───────────▼──────┐   │
│  │             Git Worktrees (Isolated Development)         │   │
│  │  worktree-dev-1/  worktree-dev-2/  worktree-dev-3/      │   │
│  └──────────────────────────────────────────────────────────┘   │
│        │                     │           │                       │
│        └─────────────────────┴───────────┘                       │
│                              │                                   │
│                    ┌─────────▼─────────┐                        │
│                    │   Main Branch     │                        │
│                    │  (Sequential      │                        │
│                    │   Merge Point)    │                        │
│                    └───────────────────┘                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### State Machine

```
Feature Request (spec.md + plan.md + tasks.md)
  ↓
Manager creates Convoys (bundle tasks by User Story)
  ↓
Manager spawns Developers (3 parallel, isolated worktrees)
  ↓
Developer claims Convoy (FIFO, no file conflicts)
  ↓
Task Lifecycle:
  ToDo → InProgress → InReview → InTests → InDocs → Done
    ↑        ↓           ↓          ↓         ↓
    └────────┴───────────┴──────────┴─────────┘
       (Rollback on quality gate failure)
  ↓
Refinery merges to main (sequential, stable)
  ↓
Librarian updates docs (convoy complete)
  ↓
Feature Done (all convoys complete)
```

---

## Agent Roles & Responsibilities

### Permanent Infrastructure (4 Agents - Always Running)

#### 1. Manager (Haiku) - Orchestrator (Mayor Pattern)

**Model:** Haiku (high frequency, low complexity)
**Session:** Permanent tmux session "manager"
**Responsibilities:**
- Poll Beads for features ready for implementation
- Create convoys from tasks.md (bundle tasks by user story)
- Spawn Developer/Tester workers via tmux
- Monitor worker health (watchdog pattern)
- Route events to CAB/Refinery/Librarian via Beads queue
- Detect feature completion (all convoys done)

**Invocation Frequency:** Continuous (30s polling for token optimization)
**Token Profile:** ~360k/hour (120 polls × 3k tokens/poll)

**Key Functions:**
- `create_convoys(feature_id)` - Parse tasks.md, create convoy records
- `spawn_developer(dev_id, convoy_id)` - Create tmux session + worktree
- `spawn_tester(tester_id, task_ids)` - Create tmux session for testing
- `monitor_agent_health()` - Check heartbeats, detect crashes/hung/stuck
- `check_feature_complete(feature_id)` - Detect all convoys done

#### 2. CAB (Haiku) - Router

**Model:** Haiku (high frequency, rule-based routing)
**Session:** Permanent tmux session "cab"
**Responsibilities:**
- Route tasks between states (ToDo → InProgress → InReview → InTests → InDocs → Done)
- Perform automated code review (InProgress → InReview)
  - Linting (eslint, pylint)
  - Type checking (tsc, mypy)
  - Cyclomatic complexity (radon, lizard)
  - Basic SAST (Semgrep)
- Enforce quality gates at each transition
- Rollback tasks on validation failure

**Invocation Frequency:** Event-driven (processes Beads queue)
**Token Profile:** ~120k/hour (60 events × 2k tokens/event estimate)

**Routing Rules:**
```
InProgress → InReview: code_review() passes
InReview → InTests: automated checks passed
InTests → InDocs: test_quality_validated = true, AC_satisfied = 100%
InDocs → Done: security_validated = true, complexity_ok = true, merged = true
```

#### 3. Refinery (Sonnet) - Merger

**Model:** Sonnet (medium frequency, merge conflict resolution)
**Session:** Permanent tmux session "refinery"
**Responsibilities:**
- Validate security before merge (SAST, dependency scan, secrets, complexity)
- Sequential merge of worktrees to main (rebase + fast-forward)
- Run regression tests after merge
- Revert merge if tests fail
- Batch merge multiple tasks from same convoy (optimization)

**Invocation Frequency:** On-demand (when tasks reach InDocs)
**Token Profile:** ~50k/merge × 5 merges/day = 250k/day

**Security Scans:**
- Semgrep (SAST)
- Trivy (dependency CVE scan)
- TruffleHog (secret detection)
- Radon/Lizard (cyclomatic complexity)

**Merge Strategy:**
```bash
git fetch worktree main:refs/heads/merge-TASK_ID
git checkout merge-TASK_ID
git rebase main
git checkout main
git merge --ff-only merge-TASK_ID
run_all_tests || git reset --hard HEAD~1
git push origin main
```

#### 4. Librarian (Sonnet) - Documentation

**Model:** Sonnet (low frequency, documentation synthesis)
**Session:** Permanent tmux session "librarian"
**Responsibilities:**
- Detect convoy completion (all tasks in convoy Done)
- Generate As-Built documentation for convoy
- Update main documentation index
- Trigger sprint retrospectives (when feature complete)
- Feed insights back to Product Owner

**Invocation Frequency:** On-demand (when convoy completes)
**Token Profile:** ~30k/convoy × 3 convoys/feature = 90k/feature

### On-Demand Workers (Spawned Per Phase)

#### 5. Developer (Sonnet) - Implementation

**Model:** Sonnet (high frequency, high complexity)
**Session:** Temporary tmux session "dev-{1-3}"
**Quantity:** 3 parallel (user-specified "infrastructure + 3 speed")
**Responsibilities:**
- Claim convoy from Beads queue (FIFO, no file conflicts)
- Implement tasks in isolated git worktree
- Write unit tests
- Mark tasks ready for review (InProgress → InReview)
- Fix issues on rollback (code review/test/security failures)

**Invocation Frequency:** Continuous during implementation phase
**Token Profile:** ~30k/task × 5 tasks/convoy = 150k/convoy

**Lifespan:** Spawned when convoy available, terminated when convoy complete

#### 6. Tester (Haiku/Sonnet) - Validation

**Model:** Haiku for simple validation, Sonnet for complex analysis
**Session:** Temporary tmux session "tester-{1-3}"
**Quantity:** 3 parallel (1:1 ratio with Developers)
**Responsibilities:**
- Run test quality formula (coverage, mutation, AC traceability)
- Mark acceptance criteria satisfied in Beads
- Mark test-quality-validated flag
- Escalate failures to Developer

**Invocation Frequency:** When tasks reach InTests state
**Token Profile:** ~20k/task × 5 tasks/convoy = 100k/convoy

**Lifespan:** Spawned when testing needed, terminated when testing complete

### Leadership Agents (Per-Feature, Low Frequency)

#### 7. Product Owner (Opus or User)

**Model:** Opus (for very low frequency, high complexity)
**Responsibilities:**
- Create feature specification (speckit:specify)
- Define acceptance criteria
- Approve feature completion (optional)

**Invocation:** Once per feature (or user performs this role manually)

#### 8. Lead Architect (Opus)

**Model:** Opus (for very low frequency, high complexity)
**Responsibilities:**
- Review spec, create technical plan (speckit:plan)
- Design module boundaries (file isolation for convoys)
- Resolve blocked tasks (escalated by Manager)
- Review failed tasks (escalated after 3 failures)

**Invocation:** Once per feature + escalations

#### 9. Scrum Master (Sonnet)

**Model:** Sonnet (for very low frequency, medium complexity)
**Responsibilities:**
- Create tasks from plan (speckit:tasks)
- Validate no file conflicts between convoys
- Set task priorities and dependencies

**Invocation:** Once per feature

---

## Infrastructure Components

### 1. Beads Extensions (State Management)

**Base:** Existing Beads installation (SQLite)

**Schema Extensions:**

```sql
-- Events table (agent communication queue)
CREATE TABLE events (
  id TEXT PRIMARY KEY,           -- bd-a1b2c
  created_at TEXT,               -- ISO 8601
  agent_id TEXT,                 -- 'cab', 'dev-001', 'tester-001'
  event_type TEXT,               -- 'ROUTE_TASK', 'CLAIM_CONVOY', 'RUN_TESTS'
  payload TEXT,                  -- JSON
  status TEXT DEFAULT 'pending'  -- pending, processing, done, failed
);
CREATE INDEX idx_agent_pending ON events(agent_id, status);

-- Convoys table (work bundles)
CREATE TABLE convoys (
  id TEXT PRIMARY KEY,           -- convoy-us1
  feature_id TEXT,               -- Links to feature
  story TEXT,                    -- User story name
  priority TEXT,                 -- P1, P2, P3
  status TEXT,                   -- available, in-progress, done
  dependencies TEXT,             -- JSON array of convoy IDs
  files TEXT,                    -- JSON array of file paths
  assignee TEXT,                 -- dev-001, dev-002, etc.
  created_at TEXT,
  started_at TEXT,
  completed_at TEXT
);

-- Task extensions (acceptance criteria)
ALTER TABLE tasks ADD COLUMN acceptance_criteria TEXT;  -- JSON array
ALTER TABLE tasks ADD COLUMN test_quality_validated BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN code_review_status TEXT;  -- passed, failed
ALTER TABLE tasks ADD COLUMN security_validated BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN complexity_ok BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN merged_to_main BOOLEAN DEFAULT FALSE;
ALTER TABLE tasks ADD COLUMN worktree TEXT;  -- worktree-dev-001
ALTER TABLE tasks ADD COLUMN last_activity TEXT;  -- Heartbeat timestamp

-- Agent sessions (health monitoring)
CREATE TABLE agent_sessions (
  agent_id TEXT PRIMARY KEY,     -- dev-001, tester-001
  agent_type TEXT,               -- developer, tester
  status TEXT,                   -- active, crashed, hung, stuck
  current_task TEXT,             -- Task currently working on
  current_convoy TEXT,           -- Convoy assigned
  worktree TEXT,                 -- Git worktree path
  started_at TEXT,
  last_activity TEXT,            -- Heartbeat
  crashed_at TEXT
);
```

### 2. tmux Wrapper Scripts

**Location:** `~/.ai-sprint/scripts/`

**Core Scripts:**

1. **manager.sh** - Permanent orchestrator
2. **cab.sh** - Permanent router
3. **refinery.sh** - Permanent merger
4. **librarian.sh** - Permanent documentor
5. **spawn-developer.sh** - Worker spawner
6. **spawn-tester.sh** - Tester spawner
7. **monitor-health.sh** - Watchdog (integrated in manager.sh)
8. **startup.sh** - Launch permanent infrastructure

**Pseudocode:** See Topic 1 & 3 documents for detailed implementations

### 3. Beads Formulas

**Location:** `.beads/formulas/`

**test-quality-check.toml:**

Validates:
- Coverage ≥80% (pytest --cov, istanbul)
- Mutation score ≥80% (mutmut, Stryker)
- AC traceability (all AC have corresponding tests)

**Execution:**
```bash
bd cook test-quality-check --var task_id=T001
```

**Output:** Marks task.test_quality_validated = true/false in Beads

### 4. Configuration Files

**Location:** `~/.ai-sprint/config/`

**agent-models.toml:**
```toml
[agents.manager]
model = "haiku"
polling_interval = 30  # seconds

[agents.cab]
model = "haiku"
polling_interval = 5  # seconds (event-driven)

[agents.refinery]
model = "sonnet"

[agents.librarian]
model = "sonnet"

[agents.developer]
model = "sonnet"
max_concurrent = 3

[agents.tester]
model = "haiku"  # or sonnet for complex validation
max_concurrent = 3
```

**validation-thresholds.toml:**
```toml
[quality]
test_coverage = 80          # %
mutation_score = 80         # %
complexity_flag = 10        # Flag for review
complexity_max = 15         # Block merge

[security]
critical_cve = 0            # Zero tolerance
high_cve = 0                # Zero tolerance
medium_cve = 5              # Max allowed (with justification)

[timeouts]
agent_hung = 300            # 5 minutes no heartbeat
task_timeout = 7200         # 2 hours max per task
test_formula_timeout = 600  # 10 minutes
merge_timeout = 300         # 5 minutes
```

---

## Quality Gates & Validation

### Definition of Done (3 Levels)

#### Task Done
- ✅ All acceptance criteria satisfied (Beads AC checklist 100%)
- ✅ Tests written and passing
- ✅ Test coverage ≥80%
- ✅ Mutation score ≥80%
- ✅ Cyclomatic complexity ≤15
- ✅ No critical/high CVEs
- ✅ Code merged to main
- ✅ Documentation updated

#### Convoy Done
- ✅ All tasks in convoy Done
- ✅ Integration tests passing
- ✅ Acceptance criteria from spec.md validated
- ✅ As-Built documentation complete
- ✅ No regressions in other convoys

#### Feature Done
- ✅ All convoys Done
- ✅ End-to-end tests passing
- ✅ Spec.md success criteria satisfied
- ✅ Performance requirements met (if defined)
- ✅ Security scan clean (feature-wide)
- ✅ Documentation published

### Quality Metrics Table

| Metric | Threshold | Enforced By | Stage | Action on Failure |
|--------|-----------|-------------|-------|-------------------|
| **Test Coverage** | 80% | Tester (formula) | InTests | Route to InProgress |
| **Mutation Score** | 80% | Tester (formula) | InTests | Route to InProgress |
| **Cyclomatic Complexity** | Flag: 10, Max: 15 | CAB (automated) | InReview | Flag: Review; Max: Route to InProgress |
| **Critical CVEs** | 0 | Refinery | InDocs | Block merge, route to InProgress |
| **High CVEs** | 0 | Refinery | InDocs | Block merge, route to InProgress |
| **Medium CVEs** | ≤5 | Refinery | InDocs | Flag for review |
| **Secrets Detected** | 0 | Refinery | InDocs | Block merge |
| **SAST Critical** | 0 | CAB (InReview) + Refinery (InDocs) | InReview, InDocs | Block merge |
| **AC Satisfaction** | 100% | Tester | InTests | Route to InProgress |

### State Transitions with Quality Gates

```
ToDo → InProgress
  [No gate]

InProgress → InReview
  [No gate - Developer triggers]

InReview → InTests
  ✓ Code review (CAB):
    - Linting clean
    - Type checking passes
    - Cyclomatic complexity ≤15
    - Basic SAST clean

InTests → InDocs
  ✓ Test quality (Tester):
    - Coverage ≥80%
    - Mutation score ≥80%
    - AC traceability 100%
    - All AC satisfied

InDocs → Done
  ✓ Security & Merge (Refinery):
    - Critical/high CVEs = 0
    - Secrets = 0
    - Complexity ≤15
    - Merge successful
    - Regression tests pass
```

---

## Coordination & Recovery

### Convoy Allocation (FIFO with File Conflict Prevention)

**Planning Phase (Prevents Conflicts):**

1. **Architect** designs module boundaries in plan.md
2. **Scrum Master** creates tasks with file isolation
3. **Automated validation** ensures no file overlap between convoys

**Example:**
```
convoy-us1: src/auth/* (no overlap)
convoy-us2: src/middleware/* (no overlap)
convoy-us3: src/db/* (no overlap)
```

**Runtime (FIFO Allocation):**

```bash
# Developer requests work
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Claims first available convoy (FIFO)
bd update $CONVOY_ID --status in-progress --assignee dev-001
```

**Result:** No merge conflicts (file isolation guaranteed at planning phase)

**Trade-off Accepted:** May slow development (Developers wait for convoys touching different files), but ensures humanless merging.

### Merge Strategy (Sequential Refinery)

**Flow:**
```
Developer completes task
  ↓
Code review passes (CAB)
  ↓
Tests pass (Tester)
  ↓
Refinery validates security
  ↓
Refinery merges to main (sequential)
  ↓
Refinery runs regression tests
  ↓
  Success → Task Done
  Failure → Revert merge, route to InProgress
```

**Optimizations:**
- Fast-forward merges (linear history)
- Batch merging (multiple tasks from same convoy)
- Pre-merge validation (Developer runs checks in worktree)

**Benefits:**
- ✅ Stable main branch (single merge point)
- ✅ No merge conflicts (sequential + file isolation)
- ❌ Bottleneck (single Refinery) - acceptable for 2-3 features/week

### Failure Recovery (Restart from Beads)

**Design Decision:** No git hooks for MVP (rare crashes don't justify complexity)

**On Agent Crash:**

1. Manager detects (no heartbeat for 5 minutes)
2. Manager kills tmux session (if hung)
3. Manager restarts session (spawn-developer.sh)
4. Agent reads Beads for context:
   ```bash
   TASK_ID=$(bd show --assignee dev-001 --status InProgress --json | jq -r '.id')
   bd show $TASK_ID --field acceptance_criteria
   cat worktree-dev-001/$(bd show $TASK_ID --field file)
   ```
5. Agent resumes work (rebuilds context from Beads + files)

**What's Lost:** Conversation history, current strategy
**Acceptable:** For rare crashes (<once/day), 30-60s context rebuild is tolerable

### Health Monitoring (Automatic Watchdog)

**Manager monitors:**

| Condition | Threshold | Action |
|-----------|-----------|--------|
| **Crash** | tmux session not found | Restart immediately |
| **Hung** | No heartbeat for 5 min | Kill + restart |
| **Stuck** | Task duration >2 hours | Mark failed, escalate to Architect, restart |
| **Test timeout** | Formula >10 min | Kill formula, route to InProgress |
| **Merge timeout** | Merge >5 min | Abort, mark conflict, notify developer |

**Escalation:** After 3 failures on same task → Architect reviews (may be too complex, AC ambiguous, fundamental issue)

---

## Complete Task Flow

### End-to-End Lifecycle (with Token Estimates)

```
1. PLANNING PHASE (Leadership Agents - Once per Feature)
   ├─ Product Owner: Create spec.md (~20k tokens)
   ├─ Lead Architect: Create plan.md, validate module boundaries (~20k tokens)
   └─ Scrum Master: Create tasks.md, validate file isolation (~15k tokens)
   = 55k tokens

2. CONVOY CREATION (Manager)
   ├─ Manager: Parse tasks.md, create convoy records (~5k tokens)
   ├─ Manager: Spawn 3 Developers (~2k tokens each = 6k)
   = 11k tokens

3. DEVELOPMENT PHASE (Developer × 3, parallel)
   ├─ Developer claims convoy (FIFO) (~1k tokens)
   ├─ Developer implements task (~30k tokens/task × 5 tasks = 150k)
   ├─ Developer marks ready for review (~1k tokens)
   = 152k tokens per Developer × 3 = 456k tokens

4. CODE REVIEW (CAB - automated)
   ├─ CAB runs linting, type check, complexity, SAST (~5k tokens/task)
   ├─ CAB routes to InTests or InProgress (~1k tokens)
   = 6k tokens/task × 15 tasks = 90k tokens

5. TESTING PHASE (Tester × 3, parallel)
   ├─ Tester runs test quality formula (~10k tokens/task)
   ├─ Tester validates AC (~5k tokens/task)
   ├─ Tester marks validated (~1k tokens/task)
   = 16k tokens/task × 5 tasks = 80k tokens per Tester × 3 = 240k tokens

6. MERGE PHASE (Refinery - sequential)
   ├─ Refinery validates security (~10k tokens/task)
   ├─ Refinery merges to main (~5k tokens/task)
   ├─ Refinery runs regression tests (~10k tokens/merge)
   = 25k tokens/task × 15 tasks = 375k tokens

7. DOCUMENTATION PHASE (Librarian)
   ├─ Librarian detects convoy complete (~2k tokens)
   ├─ Librarian generates As-Built docs (~30k tokens/convoy × 3)
   = 92k tokens

TOTAL PER FEATURE: 55k + 11k + 456k + 90k + 240k + 375k + 92k = ~1.32M tokens
```

**Revised Estimate:** ~1.32M tokens/feature (more conservative than initial 960k)

### State Diagram (Complete)

```
                    ┌──────────────┐
                    │   Feature    │
                    │   Request    │
                    └───────┬──────┘
                            │
                    ┌───────▼────────┐
                    │ Planning Phase │
                    │ (PO→Arch→SM)   │
                    └───────┬────────┘
                            │
                    ┌───────▼────────┐
                    │ Manager creates│
                    │    Convoys     │
                    └───────┬────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
         ┌────▼───┐    ┌───▼────┐   ┌───▼────┐
         │ Dev-1  │    │ Dev-2  │   │ Dev-3  │
         │Convoy 1│    │Convoy 2│   │Convoy 3│
         └────┬───┘    └───┬────┘   └───┬────┘
              │            │            │
              │      Task Lifecycle:   │
              │                        │
         ┌────▼────────────────────────▼─────┐
         │ ToDo → InProgress → InReview      │
         │   ↓        ↓           ↓          │
         │ InTests → InDocs → Done           │
         │   ↑        ↑       ↑              │
         │   └────────┴───────┘              │
         │  (Rollback on failure)            │
         └────┬─────────────────────┬────────┘
              │                     │
         ┌────▼─────┐         ┌────▼─────┐
         │ Refinery │         │Librarian │
         │  Merges  │         │   Docs   │
         └────┬─────┘         └────┬─────┘
              │                    │
              └──────────┬─────────┘
                         │
                  ┌──────▼──────┐
                  │   Feature   │
                  │   Complete  │
                  └─────────────┘
```

---

## Token Budget & Throughput

### Per-Feature Token Budget (Revised)

| Phase | Component | Tokens |
|-------|-----------|--------|
| **Planning** | PO + Architect + SM | 55k |
| **Convoy Creation** | Manager | 11k |
| **Development** | 3 Developers × 152k | 456k |
| **Code Review** | CAB automated | 90k |
| **Testing** | 3 Testers × 80k | 240k |
| **Merge** | Refinery sequential | 375k |
| **Documentation** | Librarian | 92k |
| **TOTAL** | | **~1.32M tokens** |

### Infrastructure Overhead (Permanent Agents)

**Manager:**
- Polling: 120 polls/hour × 3k tokens = 360k/hour
- Daily: 360k × 24 = 8.64M/day
- Weekly: 60.48M/week

**CAB:**
- Event-driven: ~60 events/hour × 2k tokens = 120k/hour
- Daily: 120k × 24 = 2.88M/day
- Weekly: 20.16M/week

**Refinery + Librarian:**
- On-demand: Minimal idle overhead
- Weekly: ~5M/week (estimate)

**Total Infrastructure Overhead:** ~85M tokens/week

### Estimated Throughput

**Claude Max Weekly Limit:** ~150M tokens (rough estimate, actual may vary)

**Calculation:**
```
Available tokens: 150M/week
Infrastructure overhead: 85M/week
Feature budget available: 65M/week

Features/week: 65M ÷ 1.32M = ~49 features/week (theoretical max)
```

**Realistic Estimate (with retries, iterations, overhead):**
- **Conservative:** 2-3 features/week (high quality, thorough testing)
- **Aggressive:** 5-7 features/week (simpler features, minimal rework)

**User's Current Usage:** 2-3% weekly → Plenty of headroom for 2-3 features/week target

### Token Optimization Strategies

**If hitting limits:**

1. **Reduce polling frequency:** 30s → 60s (50% reduction in Manager overhead)
2. **Use file watchers:** inotify triggers instead of polling (90% reduction)
3. **Cache context:** Don't re-read spec.md every poll (20% reduction)
4. **Batch operations:** Process multiple events per invocation (30% reduction)
5. **Optimize models:** Use Haiku for more agents (50% cost reduction)

**Target:** Start with conservative 2-3 features/week, optimize if needed.

---

## Implementation Roadmap

### Phase 1: Proof of Concept (Week 1-2)

**Goal:** Single feature end-to-end with quality gates

**Deliverables:**
1. ✅ Beads schema extensions (events, convoys, AC metadata)
2. ✅ Manager.sh (orchestrator with health monitoring)
3. ✅ CAB.sh (router with code review)
4. ✅ Refinery.sh (sequential merger with security)
5. ✅ Librarian.sh (documentation generator)
6. ✅ spawn-developer.sh, spawn-tester.sh (worker spawners)
7. ✅ test-quality-check.toml (Beads formula)
8. ✅ Configuration files (thresholds, agent models)
9. ✅ Integration with speckit (extend implement command)
10. ✅ End-to-end test: spec → plan → tasks → implement → test → merge → docs

**Success Criteria:**
- Single feature (3 convoys, 15 tasks) completes successfully
- All quality gates enforce correctly
- No manual intervention needed (fully automated)
- Token usage measured and within budget

### Phase 2: Multi-Feature Validation (Week 3-4)

**Goal:** Validate parallelism and throughput

**Deliverables:**
1. ✅ Process 3 features simultaneously
2. ✅ Validate file conflict prevention works
3. ✅ Validate convoy allocation (FIFO, dependencies)
4. ✅ Validate agent health monitoring (inject crashes)
5. ✅ Validate escalation (force 3 failures on task)
6. ✅ Measure actual token usage vs estimates
7. ✅ Measure throughput (features/week)

**Success Criteria:**
- 3 features complete in 1 week
- No merge conflicts (file isolation works)
- Health monitoring detects and recovers from crashes
- Escalation to Architect triggers correctly
- Token usage within 20% of estimates

### Phase 3: Optimization (Week 5-6)

**Goal:** Tune thresholds and optimize token usage

**Deliverables:**
1. ✅ Adjust thresholds based on Phase 2 results
   - Coverage: 80% too high/low?
   - Mutation: 80% achievable?
   - Complexity: 15 appropriate?
2. ✅ Optimize polling intervals (if token burn too high)
3. ✅ Implement file watchers (if polling overhead significant)
4. ✅ Add caching (if context re-reading overhead high)
5. ✅ Document lessons learned
6. ✅ Create runbook for operators

**Success Criteria:**
- Token usage optimized (reduce by 20-30%)
- Throughput improved (4-5 features/week achievable)
- System stable (no manual interventions for 1 week)
- Documentation complete (ready for production use)

### Phase 4: Production Deployment (Week 7+)

**Goal:** Use system for real projects

**Deliverables:**
1. ✅ Deploy to production environment
2. ✅ Monitor metrics (token usage, throughput, quality)
3. ✅ Iterate based on real usage
4. ✅ Add features as needed (e.g., git hooks if crashes become frequent)

---

## References

### Source Documents

- **Topic 1: Infrastructure & Orchestration** - `/home/artur/Scripts/AI/Sprint/artifacts/topic1_infrastructure_LOCKED.md`
- **Topic 2: Quality Gates & Validation** - `/home/artur/Scripts/AI/Sprint/artifacts/topic2_quality_gates_LOCKED.md`
- **Topic 3: Coordination & Recovery** - `/home/artur/Scripts/AI/Sprint/artifacts/topic3_coordination_LOCKED.md`

### External References

- **Gas Town GitHub:** https://github.com/steveyegge/gastown
- **Gas Town Architecture:** https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/
- **Gas Town vs Swarm-Tools:** https://gist.github.com/johnlindquist/4174127de90e1734d58fce64c6b52b62
- **OWASP Top 10 2025:** https://owasp.org/Top10/2025/
- **Cyclomatic Complexity Best Practices:** https://linearb.io/blog/cyclomatic-complexity
- **Mutation Testing:** https://en.wikipedia.org/wiki/Mutation_testing

### User Configuration

- **User Preferences:** `/home/artur/.claude/CLAUDE.md`
- **Cooperation Protocol:** `/home/artur/.claude/rules/COOPERATION.md`
- **Speckit Framework:** `~/.claude/commands/speckit/`

### Diagrams

- **Initial Diagram:** `/tmp/ai_sprint.mmd`, `/tmp/ai_sprint_diagram.png`
- **Analysis:** `/tmp/diagram_vs_roles_analysis.md`

---

## Appendix: Decision Log

### Topic 1 Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Architecture Model | Model A (Permanent Infrastructure) | Simplicity over token optimization |
| Agent Pool | 4 infrastructure + 3 developers + 3 testers | User-specified, 1:1 dev/test ratio |
| Event Queue | Beads (SQLite) | Atomic claiming, audit trail |
| tmux Integration | Infrastructure component with wrappers | User familiar, session persistence |
| Throughput Target | 2-3 features/week initially | Conservative start, measure and scale |

### Topic 2 Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| AC Storage | Beads metadata (Option C) | No duplication, queryable |
| Test Quality | Formula-based (Option A) | Repeatable, automated |
| Mutation Score | 80% | Matches coverage, industry standard |
| Complexity | Flag: 10, Max: 15 | McCabe's recommendation |
| Security CVEs | Zero critical/high | Production safety |

### Topic 3 Decisions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Convoy Allocation | FIFO with file conflict prevention | Humanless merging priority |
| Merge Strategy | Sequential Refinery with optimizations | Stable main branch |
| Code Review | Automated CAB gate (InProgress → InReview) | Enforce quality early |
| Failure Recovery | Restart from Beads (no hooks) | Rare crashes, simple recovery |
| Health Monitoring | Automatic watchdog with escalation | No manual intervention |

---

## Version History

- **v1.0** - 2026-01-25 - Initial specification (all 3 topics locked)

---

**END OF SPECIFICATION**

**Status:** Ready for implementation planning and proof of concept development.
