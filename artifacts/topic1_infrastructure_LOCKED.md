# Topic 1: Infrastructure & Orchestration - LOCKED

**Date**: 2026-01-25
**Status**: Decisions Finalized

---

## Architecture Model: Permanent Infrastructure (Model A)

### Permanent Agents (Always Running)

| Agent | Model | Role | Frequency | Token Profile |
|-------|-------|------|-----------|---------------|
| **Manager** | Haiku | Orchestrator (Mayor pattern) | Continuous poll (5s) | High freq, low complexity |
| **CAB** | Haiku | Task router (state transitions) | Continuous poll (5s) | High freq, low complexity |
| **Refinery** | Sonnet | Sequential merge manager | On-demand (merge queue) | Med freq, med complexity |
| **Librarian** | Sonnet | Documentation maintainer | On-demand (convoy complete) | Low freq, med complexity |

**Rationale:** Simplicity over token optimization. Permanent infrastructure ensures instant response, predictable orchestration.

### On-Demand Workers (Spawned Per Phase)

| Agent | Model | Role | Quantity | Spawned By |
|-------|-------|------|----------|------------|
| **Developer** | Sonnet | Implementation + unit tests | 3 parallel | Manager (per convoy) |
| **Tester** | Haiku/Sonnet | Validation + coverage | 3 parallel | Manager (1:1 ratio with Devs) |

**Rationale:** 1:1 Developer/Tester ratio ensures equal phase duration (if dev time = test time).

### Concurrent Agent Count

| Phase | Agents | Count |
|-------|--------|-------|
| Idle (no features) | Manager, CAB, Refinery, Librarian | 4 |
| Implementation | Infrastructure + 3 Developers | 7 |
| Testing | Infrastructure + 3 Testers | 7 |
| Overlap (impl + test) | Infrastructure + 3 Devs + 3 Testers | **10 peak** |

---

## Event Queue: Beads-Based (SQLite)

### Schema Extension

```sql
-- Events table for agent communication
CREATE TABLE events (
  id TEXT PRIMARY KEY,           -- bd-a1b2c (hash-based ID)
  created_at TEXT,               -- ISO 8601 timestamp
  agent_id TEXT,                 -- 'cab', 'dev-001', 'tester-001'
  event_type TEXT,               -- 'ROUTE_TASK', 'CLAIM_CONVOY', 'RUN_TESTS'
  payload TEXT,                  -- JSON with event data
  status TEXT DEFAULT 'pending'  -- pending, processing, done, failed
);

CREATE INDEX idx_agent_pending ON events(agent_id, status);
```

### Usage Pattern

**Manager writes event:**
```bash
bd create --type event --agent cab --event ROUTE_TASK \
  --payload '{"task_id":"T001","from":"InProgress","to":"InTests"}'
```

**CAB polls and processes:**
```bash
EVENT=$(bd list --type event --agent cab --status pending --limit 1 --json)
if [ -n "$EVENT" ]; then
  EVENT_ID=$(echo $EVENT | jq -r '.id')
  bd update $EVENT_ID --status processing
  # ... do routing work ...
  bd close $EVENT_ID
fi
```

**Benefits:**
- ✅ Atomic claiming (SQL transactions prevent race conditions)
- ✅ Audit trail (query event history)
- ✅ No file system clutter
- ✅ Integrates with existing Beads installation

---

## tmux Integration: Infrastructure Scripts

### Core Wrapper Scripts

**1. `manager.sh` - Permanent Coordinator**

**Purpose:** Mayor pattern orchestrator

**Responsibilities:**
- Poll Beads for features ready for implementation
- Create convoys from tasks.md (bundle tasks by user story)
- Spawn Developer/Tester workers via tmux
- Monitor worker health
- Route events to CAB/Refinery/Librarian

**Pseudocode:**
```bash
while true; do
  # Check for new features (spec.md + plan.md + tasks.md exist)
  FEATURES=$(bd list --type feature --status ready --json)

  for FEATURE in $FEATURES; do
    # Create convoys (bundle tasks by user story)
    create_convoys $FEATURE

    # Spawn 3 Developers, assign convoys
    spawn_developer 1 convoy-us1
    spawn_developer 2 convoy-us2
    spawn_developer 3 convoy-us3

    bd update $FEATURE --status in-progress
  done

  # Check for testing phase triggers
  TESTING_NEEDED=$(bd list --status InTests --json | jq 'length')
  if [ $TESTING_NEEDED -gt 0 ]; then
    spawn_testers $TESTING_NEEDED
  fi

  sleep 5
done
```

**2. `spawn-developer.sh <dev-id> <convoy-id>` - Worker Spawner**

**Purpose:** Create isolated Developer agent with git worktree

**Inputs:**
- `$1`: Developer ID (1-3)
- `$2`: Convoy ID (convoy-us1, convoy-us2, etc.)

**Outputs:**
- tmux session: `dev-<id>`
- Git worktree: `worktree-dev-<id>/`

**Pseudocode:**
```bash
DEV_ID=$1
CONVOY_ID=$2
WORKTREE_DIR="worktree-dev-${DEV_ID}"

# Create isolated git worktree (Gas Town pattern)
git worktree add $WORKTREE_DIR

# Spawn tmux session with Claude Code
tmux new-session -d -s "dev-${DEV_ID}" \
  -c "$WORKTREE_DIR" \
  "claude-code --hook 'source ~/.ai-sprint/hooks/developer.sh $CONVOY_ID'"

# Track session in Beads
bd create --type agent-session --agent dev-$DEV_ID --convoy $CONVOY_ID
```

**3. `spawn-tester.sh <tester-id> <task-ids>` - Tester Spawner**

**Purpose:** Create Tester agent for validation phase

**Inputs:**
- `$1`: Tester ID (1-3)
- `$2`: Space-separated task IDs to test

**Outputs:**
- tmux session: `tester-<id>`

**Pseudocode:**
```bash
TESTER_ID=$1
TASK_IDS=$2

tmux new-session -d -s "tester-${TESTER_ID}" \
  "claude-code --hook 'source ~/.ai-sprint/hooks/tester.sh $TASK_IDS'"

bd create --type agent-session --agent tester-$TESTER_ID --tasks "$TASK_IDS"
```

**4. System Startup Script**

**Purpose:** Launch permanent infrastructure sessions

**Pseudocode:**
```bash
# ~/.ai-sprint/startup.sh
tmux new-session -d -s "manager" "~/ai-sprint/manager.sh"
tmux new-session -d -s "cab" "~/ai-sprint/cab.sh"
tmux new-session -d -s "refinery" "~/ai-sprint/refinery.sh"
tmux new-session -d -s "librarian" "~/ai-sprint/librarian.sh"

echo "AI Sprint infrastructure started. 4 permanent agents running."
```

### Monitoring & Utilities

**5. `monitor-health.sh` - Agent Health Check (Witness Pattern)**

**Purpose:** Detect hung or failed agents

**Pseudocode:**
```bash
for SESSION in manager cab refinery librarian dev-* tester-*; do
  if tmux has-session -t $SESSION 2>/dev/null; then
    # Check if session is responsive (last activity timestamp)
    LAST_ACTIVITY=$(tmux display-message -t $SESSION -p '#{pane_activity}')
    NOW=$(date +%s)
    IDLE_TIME=$((NOW - LAST_ACTIVITY))

    if [ $IDLE_TIME -gt 300 ]; then
      echo "WARNING: $SESSION idle for ${IDLE_TIME}s"
      # Optional: restart session
    fi
  fi
done
```

**6. `aggregate-logs.sh` - Log Consolidation**

**Purpose:** Collect logs from all tmux sessions

**Pseudocode:**
```bash
mkdir -p /var/log/ai-sprint/
for SESSION in $(tmux list-sessions -F '#{session_name}'); do
  tmux pipe-pane -t $SESSION -o "cat >> /var/log/ai-sprint/${SESSION}.log"
done
```

---

## Token Budget & Throughput

### Per-Feature Token Estimate

| Phase | Component | Tokens |
|-------|-----------|--------|
| **Specification** | Lead Architect reviews spec | 20k |
| | Scrum Master creates tasks | 15k |
| | **Subtotal** | **35k** |
| **Implementation** | 3 Developers × 15 tasks × 30k | 450k |
| | Code review iterations | 50k |
| | Test quality validation | 30k |
| | **Subtotal** | **530k** |
| **Testing** | 3 Testers × 15 tasks × 20k | 300k |
| | Mutation testing | 40k |
| | **Subtotal** | **340k** |
| **Merge & Docs** | Refinery merges worktrees | 30k |
| | Librarian updates As-Built | 25k |
| | **Subtotal** | **55k** |
| **TOTAL PER FEATURE** | | **~960k tokens** |

### Infrastructure Overhead (Permanent Agents)

| Agent | Poll Frequency | Tokens/Poll | Tokens/Hour |
|-------|---------------|-------------|-------------|
| Manager | Every 5s (720/hour) | ~2k | 1.44M |
| CAB | Every 5s (720/hour) | ~1k | 0.72M |
| Refinery | Idle (event-driven) | - | Minimal |
| Librarian | Idle (event-driven) | - | Minimal |
| **Total Overhead** | | | **~2.16M/hour** |

**Daily infrastructure cost:** 2.16M × 24h = **51.84M tokens/day**

### Estimated Throughput

**Claude Max Weekly Limit:** ~50M tokens (estimated)

**Scenario Analysis:**

| Scenario | Features/Week | Feature Tokens | Infrastructure | Total | Feasible? |
|----------|---------------|----------------|----------------|-------|-----------|
| Conservative | 2-3 | 2.88M | 51.84M × 7 = 362.88M | 365.76M | ❌ Exceeds limit |
| Optimized Polling | 2-3 | 2.88M | 5M/day × 7 = 35M | 37.88M | ✅ Within limit |
| Aggressive | 5-7 | 6.72M | 35M | 41.72M | ✅ Within limit |

**Critical Insight:** Infrastructure overhead dominates. Polling every 5 seconds is expensive.

**Optimization Strategy:**
- Reduce polling frequency: 5s → 30s (6x reduction)
- Use file watchers (inotify) to trigger Manager instead of polling
- Cache context between polls (don't re-read spec.md every 5s)

**Revised Infrastructure Overhead (30s polling):**
- Manager: 240k/hour (120 polls × 2k)
- CAB: 120k/hour (120 polls × 1k)
- **Total: ~360k/hour = 8.64M/day = 60.48M/week**

**With optimization:**
- Infrastructure: 60.48M/week
- 5 features × 960k = 4.8M
- **Total: 65.28M/week** (still exceeds estimate, but closer)

**Realistic Target:**
- **Start with 2-3 features/week**
- Measure actual token usage
- Optimize polling if needed
- Scale up as we learn

---

## Decisions Summary

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **Architecture Model** | Model A (Permanent Infrastructure) | Simplicity over token optimization |
| **Permanent Agents** | 4 (Manager, CAB, Refinery, Librarian) | Instant response, predictable orchestration |
| **Developer Count** | 3 parallel | User-specified "infrastructure + 3 speed" |
| **Tester Count** | 3 parallel | 1:1 ratio with Developers (equal phase duration) |
| **Peak Concurrent** | 10 agents | 4 infrastructure + 3 devs + 3 testers |
| **Event Queue** | Beads (SQLite) | Atomic claiming, audit trail, existing install |
| **tmux Integration** | Infrastructure component | User familiar, session persistence, manual inspection |
| **Wrapper Scripts** | Part of specification | Define WHAT/WHY, pseudocode for critical paths |
| **Throughput Target** | 2-3 features/week (start) | Measure and optimize based on actuals |
| **Polling Strategy** | 30s intervals (optimized) | Balance responsiveness vs token burn |

---

## Next Steps

**Topic 1 is LOCKED.** Proceed to:

**Topic 2: Quality Gates & Validation**
- Definition of Done with acceptance criteria
- Test quality formulas (mutation score, coverage)
- Cyclomatic complexity best practices
- Security validation (OWASP, CVE)
- CAB routing rules specification

---

## References

- Gas Town GitHub: https://github.com/steveyegge/gastown
- Gas Town Architecture Analysis: https://paddo.dev/blog/gastown-two-kinds-of-multi-agent/
- User Preferences: `/home/artur/.claude/CLAUDE.md`
- Cooperation Protocol: `/home/artur/.claude/rules/COOPERATION.md`
- Speckit Framework: `~/.claude/commands/speckit/`
