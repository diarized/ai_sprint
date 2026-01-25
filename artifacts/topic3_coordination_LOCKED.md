# Topic 3: Coordination & Recovery - LOCKED

**Date**: 2026-01-25
**Status**: Decisions Finalized

---

## Convoy Allocation Strategy: FIFO with Codebase Conflict Prevention

### Core Requirement

**User Decision:** "FIFO, but Architect with Scrum Master need to prevent the situation where two developers work on the same part of the codebase - merging will be extremely difficult. I'd be happy to slow down development for the sake of easy (humanless) merging."

**Design Principle:** **Conflict prevention at planning phase, not runtime.**

### Planning Phase: File Conflict Analysis

**Architect + Scrum Master responsibilities:**

**Step 1: Architect designs clear boundaries**

When creating plan.md, Architect defines module/component boundaries:

```markdown
# plan.md - Feature: User Authentication

## Module Structure

### Module 1: Authentication Core (src/auth/)
- login.ts - Login endpoint
- session.ts - Session management
- jwt.ts - Token generation

### Module 2: Middleware (src/middleware/)
- auth-middleware.ts - Request authentication
- rate-limit.ts - Rate limiting

### Module 3: Database (src/db/)
- user-repository.ts - User CRUD operations
```

**Step 2: Scrum Master creates tasks with file isolation**

When creating tasks.md, Scrum Master ensures **each convoy touches different files**:

```markdown
# tasks.md

### Phase 3: User Story 1 - Authentication Core (Convoy convoy-us1)
- [ ] [T001] [P1] [US1] Implement login endpoint in src/auth/login.ts
- [ ] [T002] [P1] [US1] Add session management in src/auth/session.ts
- [ ] [T003] [P1] [US1] Create JWT utilities in src/auth/jwt.ts

### Phase 4: User Story 2 - Middleware (Convoy convoy-us2)
- [ ] [T004] [P2] [US2] Add auth middleware in src/middleware/auth-middleware.ts
- [ ] [T005] [P2] [US2] Add rate limiting in src/middleware/rate-limit.ts

### Phase 5: User Story 3 - Database Layer (Convoy convoy-us3)
- [ ] [T006] [P2] [US3] Implement user repository in src/db/user-repository.ts
```

**File Mapping:**
```
convoy-us1: src/auth/* (no overlap)
convoy-us2: src/middleware/* (no overlap)
convoy-us3: src/db/* (no overlap)
```

**Step 3: Scrum Master validates no file conflicts**

**Automated check during speckit:tasks:**

```bash
#!/bin/bash
# File: ~/.ai-sprint/scripts/check-file-conflicts.sh
# Called by speckit:tasks after generating tasks.md

# Extract file paths per convoy
declare -A convoy_files

while read -r convoy file; do
  convoy_files[$convoy]+="$file "
done < <(jq -r '.tasks[] | "\(.convoy) \(.file)"' tasks.json)

# Check for overlaps
for convoy1 in "${!convoy_files[@]}"; do
  for convoy2 in "${!convoy_files[@]}"; do
    if [ "$convoy1" != "$convoy2" ]; then
      # Find common files
      common=$(comm -12 \
        <(echo "${convoy_files[$convoy1]}" | tr ' ' '\n' | sort) \
        <(echo "${convoy_files[$convoy2]}" | tr ' ' '\n' | sort))

      if [ -n "$common" ]; then
        echo "ERROR: File conflict between $convoy1 and $convoy2:"
        echo "$common"
        exit 1
      fi
    fi
  done
done

echo "PASS: No file conflicts between convoys"
```

**If conflicts detected:**
```bash
ERROR: File conflict between convoy-us1 and convoy-us2:
src/auth/session.ts
```

**Resolution:** Scrum Master restructures tasks to eliminate overlap, or creates dependency (convoy-us2 blocks on convoy-us1).

### Runtime: FIFO Allocation with Dependency Enforcement

**Manager creates convoy queue (after planning validation):**

```bash
# Convoy creation (after speckit:tasks confirms no file conflicts)
bd create --type convoy --id convoy-us1 --story "Authentication Core" \
  --priority P1 --status available --dependencies "" \
  --files "src/auth/login.ts,src/auth/session.ts,src/auth/jwt.ts"

bd create --type convoy --id convoy-us2 --story "Middleware" \
  --priority P2 --status available --dependencies "" \
  --files "src/middleware/auth-middleware.ts,src/middleware/rate-limit.ts"

bd create --type convoy --id convoy-us3 --story "Database Layer" \
  --priority P2 --status available --dependencies "" \
  --files "src/db/user-repository.ts"
```

**Developer pulls from queue (FIFO, priority-aware, dependency-aware):**

```bash
# Developer-1 requests work
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Returns: convoy-us1 (created first, P1, no dependencies)

# Developer-1 claims convoy
bd update convoy-us1 --status in-progress --assignee dev-001
```

**Developer-2 and Developer-3 request work:**

```bash
# Both convoy-us2 and convoy-us3 available (same priority P2, no dependencies)

# Developer-2 requests work (FIFO)
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Returns: convoy-us2 (created before convoy-us3)

bd update convoy-us2 --status in-progress --assignee dev-002

# Developer-3 requests work
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Returns: convoy-us3 (only one left)

bd update convoy-us3 --status in-progress --assignee dev-003
```

**Result:** All 3 Developers working on **non-overlapping files**, no merge conflicts guaranteed.

### Convoy Dependency Example (Forced Sequencing)

**If Architect determines convoy-us2 REQUIRES convoy-us1 to complete first:**

```bash
# Scrum Master creates dependency
bd create --type convoy --id convoy-us2 --story "Middleware" \
  --priority P2 --status available \
  --dependencies "convoy-us1" \
  --files "src/middleware/auth-middleware.ts,src/middleware/rate-limit.ts"
```

**Runtime behavior:**

```bash
# Developer-2 requests work while convoy-us1 is in-progress
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Returns: convoy-us3 (convoy-us2 is blocked by dependency on convoy-us1)

# After convoy-us1 completes, convoy-us2 becomes available
bd update convoy-us1 --status done

# Developer-2 requests work again
CONVOY=$(bd list --type convoy --status available \
  --no-unmet-dependencies \
  --sort created_at \
  --limit 1 --json)

# Returns: convoy-us2 (dependency met)
```

### Slowing Development for Merge Safety

**User preference:** "I'd be happy to slow down development for the sake of easy (humanless) merging."

**Implications:**

**Scenario: 3 Developers, 5 Convoys**

**Without file conflict prevention:**
```
Time 0: Dev-1 claims convoy-us1, Dev-2 claims convoy-us2, Dev-3 claims convoy-us3
Time 2h: All 3 finish, all edit src/auth/session.ts → MERGE CONFLICT
```

**With file conflict prevention (may slow down):**
```
Time 0: Dev-1 claims convoy-us1 (touches src/auth/*)
        Dev-2 claims convoy-us2 (touches src/middleware/*)
        Dev-3 claims convoy-us3 (touches src/db/*)

        convoy-us4 and convoy-us5 ALSO touch src/auth/*
        → Blocked (wait for convoy-us1 to finish)

Time 2h: convoy-us1 done, convoy-us4 becomes available
         Dev-1 claims convoy-us4 (touches src/auth/*)

Time 4h: All finish, ZERO MERGE CONFLICTS
```

**Trade-off accepted:** Some Developers may wait for convoys instead of claiming immediately, BUT merges are guaranteed conflict-free.

---

## Merge Strategy: Sequential Refinery with Code Review Gate

### Updated Flow (User Decision)

**User-specified flow:**
```
Developer completes task
  → Code review passes
  → Tests pass
  → Refinery queues merge
  → Sequential merge to main
```

### Detailed State Machine with Code Review

**Complete task lifecycle:**

```
ToDo → InProgress → InReview → InTests → InDocs → Done
  ↑        ↓           ↓          ↓         ↓
  └────────┴───────────┴──────────┴─────────┘
     (Rollback on failure at any stage)
```

### State: InReview (Code Review Gate)

**Triggered when:** Developer marks task complete

**Who reviews:** CAB performs automated code review (static analysis + AI review)

**Automated Code Review Checks:**

```bash
#!/bin/bash
# cab-code-review.sh - Automated code review

code_review() {
  TASK_ID=$1
  WORKTREE=$(bd show $TASK_ID --field worktree)
  FILE=$(bd show $TASK_ID --field file)

  cd $WORKTREE

  # 1. Code Style/Linting
  echo "Running linter..."
  eslint $FILE --format json > lint-${TASK_ID}.json
  LINT_ERRORS=$(jq '.[] | select(.errorCount > 0) | .errorCount' lint-${TASK_ID}.json | paste -sd+ | bc)

  if [ $LINT_ERRORS -gt 0 ]; then
    echo "FAIL: $LINT_ERRORS linting errors"
    bd update $TASK_ID --code-review-status failed \
      --code-review-reason "Linting: $LINT_ERRORS errors"
    return 1
  fi

  # 2. Type Safety (TypeScript/Python/etc.)
  echo "Checking type safety..."
  tsc --noEmit $FILE > typecheck-${TASK_ID}.txt 2>&1

  if [ $? -ne 0 ]; then
    echo "FAIL: Type errors detected"
    bd update $TASK_ID --code-review-status failed \
      --code-review-reason "Type safety violations"
    return 1
  fi

  # 3. Code Complexity (from Topic 2)
  echo "Checking cyclomatic complexity..."
  radon cc $FILE -a -j > complexity-${TASK_ID}.json
  MAX_COMPLEXITY=$(jq '[.. | .complexity? // 0] | max' complexity-${TASK_ID}.json)

  if [ $MAX_COMPLEXITY -gt 15 ]; then
    echo "FAIL: Max complexity $MAX_COMPLEXITY > 15"
    bd update $TASK_ID --code-review-status failed \
      --code-review-reason "Complexity $MAX_COMPLEXITY > 15"
    return 1
  fi

  # 4. Security Patterns (basic SAST)
  echo "Running security scan..."
  semgrep --config=auto --severity ERROR $FILE --json > sast-${TASK_ID}.json
  SAST_ERRORS=$(jq '.results | length' sast-${TASK_ID}.json)

  if [ $SAST_ERRORS -gt 0 ]; then
    echo "FAIL: $SAST_ERRORS security issues"
    bd update $TASK_ID --code-review-status failed \
      --code-review-reason "Security: $SAST_ERRORS critical findings"
    return 1
  fi

  # 5. Acceptance Criteria Alignment (AI review - optional)
  # Uses Claude to check if code implements AC correctly
  # (Can be skipped for MVP, rely on Tester validation)

  # All checks passed
  echo "PASS: Code review approved"
  bd update $TASK_ID --code-review-status passed \
    --code-reviewed-at $(date -Iseconds) \
    --code-reviewed-by cab

  return 0
}
```

**CAB routing with code review:**

```bash
# CAB receives event: InProgress → InReview
case "$FROM_STATE-$TO_STATE" in

  "InProgress-InReview")
    # Developer marks task ready for review
    if code_review $TASK_ID; then
      bd update $TASK_ID --status InReview
      # Automatically proceed to InTests (no manual approval needed)
      bd create --type event --agent cab --event ROUTE_TASK \
        --payload "{\"task\":\"$TASK_ID\",\"from\":\"InReview\",\"to\":\"InTests\"}"
    else
      # Code review failed, route back to InProgress
      REASON=$(bd show $TASK_ID --field code-review-reason)
      bd update $TASK_ID --status InProgress --reason "$REASON"
      notify_developer $TASK_ID "Code review failed: $REASON"
    fi
    ;;

  "InReview-InTests")
    # Code review passed, proceed to testing
    bd update $TASK_ID --status InTests
    notify_tester $TASK_ID
    ;;
esac
```

### State: InTests (Test Validation)

**Tester runs test quality formula (from Topic 2):**

```bash
# Tester receives task, runs formula
bd cook test-quality-check --var task_id=$TASK_ID

# Formula validates:
# - Coverage >80%
# - Mutation score >80%
# - AC traceability

# If pass:
bd update $TASK_ID --test-quality-validated true --status ready-for-docs

# CAB routes to InDocs
bd create --type event --agent cab --event ROUTE_TASK \
  --payload "{\"task\":\"$TASK_ID\",\"from\":\"InTests\",\"to\":\"InDocs\"}"
```

### State: InDocs (Pre-Merge Validation & Queue)

**Refinery receives task, validates and queues merge:**

```bash
#!/bin/bash
# refinery.sh - Sequential merge manager

while true; do
  # Poll for tasks ready to merge
  TASK=$(bd list --status InDocs --limit 1 --json)

  if [ -n "$TASK" ]; then
    TASK_ID=$(echo $TASK | jq -r '.id')
    WORKTREE=$(bd show $TASK_ID --field worktree)
    ASSIGNEE=$(bd show $TASK_ID --field assignee)

    echo "Processing merge for $TASK_ID from $WORKTREE"

    # Pre-merge validation (security + complexity from Topic 2)
    if ! validate_security $TASK_ID; then
      echo "FAIL: Security validation failed"
      bd update $TASK_ID --status InProgress \
        --reason "Security validation failed"
      continue
    fi

    # Attempt merge
    cd /path/to/main-repo

    # Fetch latest from worktree
    git fetch ../worktrees/$WORKTREE main:refs/heads/merge-$TASK_ID

    # Rebase onto main (ensures clean history)
    git checkout merge-$TASK_ID
    git rebase main

    if [ $? -ne 0 ]; then
      echo "FAIL: Rebase conflict"
      bd update $TASK_ID --status InProgress \
        --reason "Merge conflict detected, manual resolution needed"
      git rebase --abort
      continue
    fi

    # Fast-forward merge (clean, linear history)
    git checkout main
    git merge --ff-only merge-$TASK_ID

    if [ $? -ne 0 ]; then
      echo "FAIL: Fast-forward merge failed"
      bd update $TASK_ID --status InProgress \
        --reason "Cannot fast-forward, rebase required"
      continue
    fi

    # Run full test suite on main (regression check)
    if ! run_all_tests; then
      echo "FAIL: Tests failed on main after merge"
      git reset --hard HEAD~1  # Revert merge
      bd update $TASK_ID --status InProgress \
        --reason "Tests failed after merge (regression)"
      continue
    fi

    # Push to main
    git push origin main

    # Mark task as merged
    bd update $TASK_ID --merged-to-main true \
      --merged-at $(date -Iseconds) \
      --merged-by refinery \
      --status Done

    echo "SUCCESS: $TASK_ID merged to main"

    # Notify Librarian (convoy may be complete)
    check_convoy_complete $TASK_ID
  fi

  sleep 10  # Poll every 10 seconds
done
```

### Optimizations (User Approved)

**1. Pre-merge validation in worktree:**

Developer runs validation BEFORE requesting merge:

```bash
# Developer completes task, runs pre-merge checks
cd worktree-dev-001/
./scripts/pre-merge-check.sh

# Includes:
# - Linting
# - Type checking
# - Unit tests
# - Basic security scan

# Only if all pass, mark ready for review
bd update $TASK_ID --status ready-for-review
```

**2. Fast-forward merges (linear history):**

Refinery uses `git merge --ff-only` to ensure clean history (no merge commits).

**3. Batching (optional optimization):**

If multiple tasks from same convoy are ready, Refinery can batch merge:

```bash
# Check if multiple tasks from same convoy are ready
CONVOY=$(bd show $TASK_ID --field convoy)
READY_TASKS=$(bd list --convoy $CONVOY --status InDocs --json)

if [ $(echo $READY_TASKS | jq 'length') -gt 1 ]; then
  echo "Batch merging $(echo $READY_TASKS | jq 'length') tasks from $CONVOY"

  # Merge all in sequence
  for TASK in $(echo $READY_TASKS | jq -r '.[].id'); do
    merge_task $TASK
  done
fi
```

**Benefits:**
- ✅ Reduces merge overhead (single rebase + test run per convoy)
- ✅ Maintains sequential merging (no conflicts)

---

## Failure Recovery: Restart from Beads State (No Hooks)

### Design Decision (User Approved)

**User decision:** "No frequent crashes, please implement per your recommendation."

**Recommendation:** Skip git hooks for MVP. Use Beads state for resumption.

### Restart Workflow

**Agent crash scenario:**

```bash
# Developer-1 working on T001
dev-001: Implementing login endpoint... [CONNECTION LOST]

# tmux session "dev-001" exits

# Manager detects crash (health monitor, see below)
Manager: Agent dev-001 non-responsive for 60s

# Manager restarts session
tmux new-session -d -s "dev-001" \
  "claude-code --hook 'source ~/.ai-sprint/hooks/developer.sh'"

# Restarted agent reads Beads for context
dev-001: What was I working on?
dev-001: bd show --assignee dev-001 --status InProgress --json

# Returns: Task T001 (convoy-us1, file: src/auth/login.ts)

dev-001: bd show T001 --field acceptance_criteria --json
# AC1: Accepts email+password via POST
# AC2: Returns JWT token on success
# AC3: Returns 401 on invalid credentials
# AC4: Rate limited to 5 attempts/minute

dev-001: Reading current code state...
dev-001: cat worktree-dev-001/src/auth/login.ts

# Agent sees partially implemented code
dev-001: I see login endpoint is started but rate limiting not implemented yet.
dev-001: Continuing from where previous session left off...
```

**No special hooks needed:** Beads + git state + file system provide sufficient context.

### What Gets Lost vs Preserved

| Context Type | Preserved | Lost | Recovery Method |
|--------------|-----------|------|-----------------|
| **Task assignment** | ✅ Beads (assignee field) | - | Query Beads |
| **Acceptance criteria** | ✅ Beads metadata | - | Query Beads |
| **Files being edited** | ✅ Git worktree | - | Read file system |
| **Code already written** | ✅ Git commits | - | Read git log |
| **Conversation history** | ❌ Lost | LLM context | Agent re-reads spec/plan |
| **Current strategy** | ❌ Lost | Agent's reasoning | Agent re-analyzes from code |
| **Next steps plan** | ❌ Lost | Agent's intent | Agent re-plans from AC |

**Acceptable for rare crashes (<once per day):** Agent spends 30-60s rebuilding context, then continues.

**Not acceptable for frequent crashes:** If crashes happen hourly, context rebuild overhead becomes significant (consider implementing hooks).

---

## Agent Health Monitoring: Automatic Watchdog

### Design Requirement (User Decision)

**User decision:** "Nothing manual please. You can use many concepts and tools to make it automatic. Watchdogs, timeout etc."

### Watchdog Implementation (Witness Pattern)

**Location:** Manager includes health monitoring loop

```bash
#!/bin/bash
# manager.sh - Includes health monitoring

# Health check interval
HEALTH_CHECK_INTERVAL=60  # Check every 60 seconds

# Timeout thresholds
AGENT_TIMEOUT=300         # 5 minutes of inactivity = hung
AGENT_MAX_TASK_TIME=7200  # 2 hours per task = stuck

# Health monitoring function
monitor_agent_health() {
  # Get all active agent sessions
  AGENTS=$(bd list --type agent-session --status active --json)

  for AGENT in $(echo $AGENTS | jq -r '.[].agent_id'); do
    # Check if tmux session exists
    if ! tmux has-session -t $AGENT 2>/dev/null; then
      echo "WARNING: Agent $AGENT session not found (crashed?)"
      handle_agent_crash $AGENT
      continue
    fi

    # Check last activity timestamp
    LAST_ACTIVITY=$(bd show --agent $AGENT --field last_activity)
    NOW=$(date +%s)
    LAST_ACTIVITY_TS=$(date -d "$LAST_ACTIVITY" +%s)
    IDLE_TIME=$((NOW - LAST_ACTIVITY_TS))

    if [ $IDLE_TIME -gt $AGENT_TIMEOUT ]; then
      echo "WARNING: Agent $AGENT idle for ${IDLE_TIME}s (threshold: ${AGENT_TIMEOUT}s)"
      handle_agent_hung $AGENT
      continue
    fi

    # Check task duration (prevent infinite loops)
    TASK_ID=$(bd show --agent $AGENT --field current_task)
    if [ -n "$TASK_ID" ]; then
      TASK_STARTED=$(bd show $TASK_ID --field started_at)
      TASK_STARTED_TS=$(date -d "$TASK_STARTED" +%s)
      TASK_DURATION=$((NOW - TASK_STARTED_TS))

      if [ $TASK_DURATION -gt $AGENT_MAX_TASK_TIME ]; then
        echo "WARNING: Agent $AGENT on task $TASK_ID for ${TASK_DURATION}s (threshold: ${AGENT_MAX_TASK_TIME}s)"
        handle_agent_stuck $AGENT $TASK_ID
        continue
      fi
    fi
  done
}

# Crash recovery
handle_agent_crash() {
  AGENT=$1
  echo "RECOVERY: Restarting crashed agent $AGENT"

  # Get agent's current task
  TASK_ID=$(bd show --agent $AGENT --field current_task)
  CONVOY=$(bd show --agent $AGENT --field current_convoy)

  # Mark session as crashed
  bd update --agent $AGENT --status crashed --crashed-at $(date -Iseconds)

  # Restart agent session
  if [[ $AGENT == dev-* ]]; then
    DEV_ID=${AGENT#dev-}
    spawn_developer $DEV_ID $CONVOY
  elif [[ $AGENT == tester-* ]]; then
    TESTER_ID=${AGENT#tester-}
    TASKS=$(bd show --agent $AGENT --field assigned_tasks)
    spawn_tester $TESTER_ID "$TASKS"
  fi

  echo "RECOVERY: Agent $AGENT restarted"
}

# Hung agent recovery
handle_agent_hung() {
  AGENT=$1
  echo "RECOVERY: Agent $AGENT appears hung, killing and restarting"

  # Kill tmux session
  tmux kill-session -t $AGENT

  # Same recovery as crash
  handle_agent_crash $AGENT
}

# Stuck agent recovery (infinite loop on task)
handle_agent_stuck() {
  AGENT=$1
  TASK_ID=$2
  echo "RECOVERY: Agent $AGENT stuck on task $TASK_ID for too long"

  # Mark task as failed (excessive duration)
  bd update $TASK_ID --status failed \
    --failure-reason "Agent stuck (exceeded ${AGENT_MAX_TASK_TIME}s)" \
    --failed-at $(date -Iseconds)

  # Escalate to Architect for review (task may be too complex)
  bd create --type event --agent architect --event REVIEW_FAILED_TASK \
    --payload "{\"task\":\"$TASK_ID\",\"reason\":\"Agent timeout\"}"

  # Kill and restart agent
  tmux kill-session -t $AGENT
  handle_agent_crash $AGENT
}

# Main health monitoring loop
monitor_health_loop() {
  while true; do
    monitor_agent_health
    sleep $HEALTH_CHECK_INTERVAL
  done
}

# Run in background
monitor_health_loop &
HEALTH_MONITOR_PID=$!
```

### Activity Heartbeat (Agent Side)

**Agents update "last_activity" timestamp:**

```bash
# developer.sh - Agent heartbeat

update_activity_heartbeat() {
  AGENT_ID=$1
  bd update --agent $AGENT_ID --last-activity $(date -Iseconds)
}

# Update heartbeat every 30 seconds
while true; do
  update_activity_heartbeat $AGENT_ID
  sleep 30
done &

HEARTBEAT_PID=$!
```

**Heartbeat ensures:**
- Manager can detect hung agents (no heartbeat for >5 minutes)
- Distinguishes crash (no heartbeat) from slow work (heartbeat present)

### Timeout Configuration

| Scenario | Threshold | Action |
|----------|-----------|--------|
| **Agent crash** | No tmux session | Restart immediately |
| **Agent hung** | No heartbeat for 5 min | Kill + restart |
| **Task timeout** | Task duration >2 hours | Mark failed, escalate, restart agent |
| **Test timeout** | Test formula >10 min | Kill formula, route task back to InProgress |
| **Merge timeout** | Merge operation >5 min | Abort merge, mark conflict, notify developer |

### Escalation Path (For Failed Tasks)

**If task fails repeatedly (e.g., 3 restarts):**

```bash
FAILURE_COUNT=$(bd show $TASK_ID --field failure_count)

if [ $FAILURE_COUNT -ge 3 ]; then
  echo "ESCALATION: Task $TASK_ID failed 3 times, escalating to Architect"

  # Mark task as blocked
  bd update $TASK_ID --status blocked \
    --blocked-reason "Repeated agent failures (${FAILURE_COUNT} attempts)"

  # Notify Architect for manual review
  bd create --type event --agent architect --event REVIEW_BLOCKED_TASK \
    --payload "{\"task\":\"$TASK_ID\",\"failures\":$FAILURE_COUNT}"

  # Human intervention may be needed at this point
  # (e.g., task is too complex, AC is ambiguous, code has fundamental issue)
fi
```

---

## Summary: Coordination & Recovery Decisions

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Convoy Allocation** | FIFO with codebase conflict prevention | Planning-phase file isolation prevents merge conflicts |
| **Priority Tiebreaker** | FIFO (created_at timestamp) | Simple, predictable, no complex heuristics |
| **File Conflict Prevention** | Architect + Scrum Master validate at planning | Slow down development to ensure humanless merging |
| **Merge Strategy** | Sequential Refinery with code review gate | Single merge point, stable main branch |
| **Code Review** | Automated (linting, types, complexity, SAST) | Inserted between InProgress and InTests |
| **Failure Recovery** | Restart from Beads state (no hooks) | Rare crashes don't justify hook complexity |
| **Health Monitoring** | Automatic watchdog with timeouts | Manager detects crashes/hung/stuck, auto-restarts |
| **Escalation** | After 3 failures, escalate to Architect | Human intervention for genuinely stuck tasks |

---

## Complete Task Flow (All Topics Integrated)

### End-to-End Task Lifecycle

```
1. Planning Phase (Before Development)
   ↓
   Architect creates plan.md (module boundaries)
   ↓
   Scrum Master creates tasks.md (file isolation validated)
   ↓
   Manager creates convoys (FIFO queue, dependencies)

2. Development Phase
   ↓
   Developer claims convoy (FIFO, no file conflicts)
   ↓
   Developer implements in isolated worktree
   ↓
   Developer marks ready for review (InProgress → InReview)
   ↓
   CAB runs code review (linting, types, complexity, SAST)
     ├─ FAIL → Route back to InProgress
     └─ PASS → Route to InTests

3. Testing Phase
   ↓
   Tester claims task (InTests)
   ↓
   Tester runs test quality formula (coverage, mutation, AC traceability)
     ├─ FAIL → Route back to InProgress
     └─ PASS → Route to InDocs

4. Merge Phase
   ↓
   Refinery validates security (SAST, dependency scan, secrets)
     ├─ FAIL → Route back to InProgress
     └─ PASS → Merge to main
   ↓
   Refinery runs regression tests
     ├─ FAIL → Revert merge, route back to InProgress
     └─ PASS → Mark Done

5. Documentation Phase
   ↓
   Librarian checks if convoy complete (all tasks Done)
     ├─ Not complete → Wait
     └─ Complete → Update As-Built docs

6. Feature Complete
   ↓
   Manager checks if all convoys Done
     ├─ Not complete → Wait
     └─ Complete → Feature Done
```

### State Transition Matrix

| From State | To State | Trigger | Validator | Success → | Failure → |
|------------|----------|---------|-----------|-----------|-----------|
| **ToDo** | InProgress | Developer claims convoy | None | InProgress | N/A |
| **InProgress** | InReview | Developer completes implementation | None | InReview | N/A |
| **InReview** | InTests | Code review validates | CAB (automated) | InTests | InProgress |
| **InTests** | InDocs | Test quality validates | Tester (formula) | InDocs | InProgress |
| **InDocs** | Done | Security + merge validates | Refinery (automated) | Done | InProgress |

### Rollback Paths (Quality Enforcement)

```
InReview (code review fail) → InProgress
   ↓
   Developer receives notification: "Linting errors: 5"
   Developer fixes issues
   Developer marks ready for review again

InTests (test quality fail) → InProgress
   ↓
   Developer receives notification: "Coverage 65% < 80%"
   Developer adds tests
   Developer marks ready for review again

InDocs (security fail) → InProgress
   ↓
   Developer receives notification: "Critical SAST finding: SQL injection"
   Developer fixes vulnerability
   Developer marks ready for review again
```

---

## Convoy Completion & Feature Completion

### Convoy Completion Detection

**Librarian checks convoy status:**

```bash
# Librarian polling loop
while true; do
  # Get all active convoys
  CONVOYS=$(bd list --type convoy --status in-progress --json)

  for CONVOY in $(echo $CONVOYS | jq -r '.[].id'); do
    # Check if all tasks in convoy are Done
    TOTAL_TASKS=$(bd list --convoy $CONVOY --type task --json | jq 'length')
    DONE_TASKS=$(bd list --convoy $CONVOY --type task --status Done --json | jq 'length')

    if [ $TOTAL_TASKS -eq $DONE_TASKS ]; then
      echo "Convoy $CONVOY complete: $DONE_TASKS/$TOTAL_TASKS tasks Done"

      # Update convoy status
      bd update $CONVOY --status done --completed-at $(date -Iseconds)

      # Generate As-Built documentation for convoy
      generate_convoy_docs $CONVOY

      # Check if feature complete (all convoys done)
      check_feature_complete $(bd show $CONVOY --field feature)
    fi
  done

  sleep 30
done
```

### Feature Completion Detection

**Manager checks feature status:**

```bash
check_feature_complete() {
  FEATURE=$1

  # Get all convoys for feature
  TOTAL_CONVOYS=$(bd list --type convoy --feature $FEATURE --json | jq 'length')
  DONE_CONVOYS=$(bd list --type convoy --feature $FEATURE --status done --json | jq 'length')

  if [ $TOTAL_CONVOYS -eq $DONE_CONVOYS ]; then
    echo "Feature $FEATURE complete: $DONE_CONVOYS/$TOTAL_CONVOYS convoys Done"

    # Mark feature as complete
    bd update --feature $FEATURE --status done --completed-at $(date -Iseconds)

    # Notify Product Owner (optional)
    bd create --type event --agent product-owner --event FEATURE_COMPLETE \
      --payload "{\"feature\":\"$FEATURE\"}"

    # Cleanup: Remove temporary worktrees
    cleanup_feature_worktrees $FEATURE
  fi
}

cleanup_feature_worktrees() {
  FEATURE=$1

  # Get all worktrees for feature
  WORKTREES=$(bd list --type agent-session --feature $FEATURE --json | jq -r '.[].worktree')

  for WORKTREE in $WORKTREES; do
    if [ -d "$WORKTREE" ]; then
      echo "Removing worktree: $WORKTREE"
      git worktree remove $WORKTREE
    fi
  done
}
```

---

## Integration with Topics 1 & 2

### Agent Count Update (with Code Review)

**From Topic 1:** 4 permanent + 3 Developers + 3 Testers = 10 peak

**Code review is automated (CAB), no new agents needed.**

**Updated count:** Still 10 agents max (no change)

### Quality Gates Integration

**From Topic 2:** Coverage 80%, Mutation 80%, Complexity ≤15, Zero CVEs

**All enforced at:**
- InReview: Complexity ≤15 (CAB)
- InTests: Coverage 80%, Mutation 80% (Tester formula)
- InDocs: Zero critical/high CVEs (Refinery)

**No gaps:** Every quality metric has enforcement point.

---

## Next Steps

**All 3 Topics LOCKED.** Ready for:

1. **Implementation Planning**
   - Script development (manager.sh, spawn-*.sh, cab.sh, refinery.sh, librarian.sh)
   - Beads schema extension (events, convoys, AC metadata)
   - Formula creation (test-quality-check.toml)
   - Configuration files (thresholds, agent models)

2. **Proof of Concept**
   - Single feature end-to-end (spec → plan → tasks → implement → test → merge → docs)
   - Validate all quality gates work
   - Measure token usage

3. **Iteration & Optimization**
   - Adjust thresholds based on PoC results
   - Optimize polling intervals if token burn too high
   - Add hooks if crash recovery becomes pain point

---

## References

- Gas Town GitHub: https://github.com/steveyegge/gastown
- Gas Town Architecture: https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/
- Beads Framework: User's existing installation
- Speckit Framework: `~/.claude/commands/speckit/`
- Topic 1: Infrastructure & Orchestration
- Topic 2: Quality Gates & Validation
