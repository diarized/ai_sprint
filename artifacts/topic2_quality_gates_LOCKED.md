# Topic 2: Quality Gates & Validation - LOCKED

**Date**: 2026-01-25
**Status**: Decisions Finalized

---

## Definition of Done (Task/Convoy/Feature Levels)

### Task-Level Done Criteria

**A task is Done when ALL of the following are satisfied:**

| Criterion | Validation Method | Owner |
|-----------|------------------|-------|
| **All Acceptance Criteria met** | Beads AC checklist (all marked satisfied) | Developer + Tester |
| **Tests written and passing** | Test suite execution (exit code 0) | Developer |
| **Test coverage >80%** | Coverage report (pytest --cov, istanbul) | Tester |
| **Mutation score >80%** | Mutation testing (mutmut, Stryker) | Tester |
| **Cyclomatic complexity ≤15** | Static analysis (radon, lizard) | CAB (automated) |
| **No critical/high CVEs** | Security scan (Semgrep, Trivy, TruffleHog) | Refinery (pre-merge) |
| **Code merged to main** | Git merge successful (no conflicts) | Refinery |
| **Documentation updated** | Inline comments, README changes | Developer |

**State Transition:** InDocs → Done (after all criteria validated)

### Convoy-Level Done Criteria

**A convoy (user story) is Done when ALL of the following are satisfied:**

| Criterion | Validation Method | Owner |
|-----------|------------------|-------|
| **All tasks in convoy Done** | Beads query: `bd list --convoy <id> --status done` | Manager |
| **Integration tests passing** | Test suite for user story scenarios | Tester |
| **Acceptance criteria from spec.md validated** | Manual verification against spec.md | Product Owner (optional) or Tester |
| **As-Built documentation complete** | Librarian has updated docs for user story | Librarian |
| **No regressions in other convoys** | Full regression test suite passing | Tester (post-merge) |

**State Transition:** InDocs → Convoy-Done (after Librarian documentation)

### Feature-Level Done Criteria

**A feature is Done when ALL of the following are satisfied:**

| Criterion | Validation Method | Owner |
|-----------|------------------|-------|
| **All convoys Done** | Beads query: `bd list --feature <id> --type convoy --status done` | Manager |
| **End-to-end tests passing** | Full feature workflow validation | Tester |
| **Spec.md acceptance criteria satisfied** | Verify against spec.md success criteria | Product Owner or Lead Architect |
| **Performance requirements met** | Load testing, response time validation | Tester (if performance AC exists) |
| **Security scan clean** | Zero critical/high CVEs across feature | Refinery |
| **Documentation published** | Librarian has finalized As-Built docs | Librarian |
| **Deployment successful** | Feature deployed to target environment | Manager (optional, depends on workflow) |

**State Transition:** All Convoys Done → Feature-Done (ready for release)

---

## Acceptance Criteria: Beads Metadata Storage

### Design Decision: Option C (Beads Metadata)

**Rationale:**
- ✅ No duplication (single source of truth in Beads)
- ✅ Queryable (structured data, SQL-accessible)
- ✅ Traceable (AC changes tracked in Beads history)
- ✅ Keeps tasks.md readable (summary only, full AC in DB)

### Beads Schema Extension

**Extend Beads task type with AC fields:**

```sql
-- Task table already exists in Beads
-- Add AC-related columns via custom fields

-- Example task record:
{
  "id": "T001",
  "type": "task",
  "priority": "P1",
  "story": "US1",
  "description": "Implement login endpoint",
  "file": "src/auth/login.ts",
  "status": "InProgress",
  "assignee": "dev-001",

  -- NEW: Acceptance Criteria
  "acceptance_criteria": [
    {
      "id": "AC1",
      "description": "Accepts email+password via POST",
      "satisfied": false,
      "validated_by": null,
      "validated_at": null
    },
    {
      "id": "AC2",
      "description": "Returns JWT token on success",
      "satisfied": false,
      "validated_by": null,
      "validated_at": null
    },
    {
      "id": "AC3",
      "description": "Returns 401 on invalid credentials",
      "satisfied": false,
      "validated_by": null,
      "validated_at": null
    },
    {
      "id": "AC4",
      "description": "Rate limited to 5 attempts/minute",
      "satisfied": false,
      "validated_by": null,
      "validated_at": null
    }
  ]
}
```

### Usage Workflow

**1. Scrum Master creates task with AC (from spec.md):**

```bash
# speckit:tasks extracts AC from spec.md and embeds in Beads
bd create --type task --id T001 --priority P1 --story US1 \
  --description "Implement login endpoint" \
  --file "src/auth/login.ts" \
  --ac "Accepts email+password via POST" \
  --ac "Returns JWT token on success" \
  --ac "Returns 401 on invalid credentials" \
  --ac "Rate limited to 5 attempts/minute"
```

**2. Developer claims task and views AC:**

```bash
# Developer reads AC to understand requirements
bd show T001 --field acceptance_criteria --json | jq -r '.[].description'

# Output:
# Accepts email+password via POST
# Returns JWT token on success
# Returns 401 on invalid credentials
# Rate limited to 5 attempts/minute
```

**3. Tester validates AC:**

```bash
# Tester runs tests, marks AC as satisfied
bd ac-satisfy T001 AC1 --validator tester-001
bd ac-satisfy T001 AC2 --validator tester-001
bd ac-satisfy T001 AC3 --validator tester-001
bd ac-satisfy T001 AC4 --validator tester-001

# Check satisfaction status
bd ac-status T001 --json
# Output: {"total": 4, "satisfied": 4, "percentage": 100}
```

**4. CAB checks AC before routing to Done:**

```bash
# CAB queries AC satisfaction
AC_STATUS=$(bd ac-status T001 --json)
SATISFIED=$(echo $AC_STATUS | jq -r '.percentage')

if [ $SATISFIED -eq 100 ]; then
  # All AC satisfied, route to Done
  bd update T001 --status Done
else
  # AC incomplete, route back to InProgress
  bd update T001 --status InProgress --reason "AC not satisfied: ${SATISFIED}%"
fi
```

### tasks.md Display Format

**tasks.md shows summary, full AC in Beads:**

```markdown
### Phase 3: User Story 1 - User Authentication

- [ ] [T001] [P1] [US1] Implement login endpoint in src/auth/login.ts
  **AC**: 4 criteria (view: `bd show T001 --ac`)

- [ ] [T002] [P1] [US1] Write unit tests for login in tests/auth/login.test.ts
  **AC**: 4 criteria (view: `bd show T002 --ac`)
```

**Benefits:**
- Readable tasks.md (no clutter)
- Full AC queryable via `bd show`
- Developer/Tester can programmatically check AC

---

## Test Quality Validation: Formula-Based Automation

### Design Decision: Option A (Formula-Based)

**Rationale:**
- ✅ Repeatable (same validation every task)
- ✅ Automated (no manual checklist)
- ✅ Traceable (formula execution logged in Beads)
- ✅ Configurable (update formula without changing agent code)

### Beads Formula: test-quality-check.toml

**Location:** `.beads/formulas/test-quality-check.toml`

```toml
[formula]
name = "test-quality-check"
version = "1.0"
description = "Validates test quality before routing to InDocs"
author = "AI Sprint System"

# Global variables (can be overridden per execution)
[variables]
coverage_threshold = 80
mutation_threshold = 80
task_id = ""  # Passed at runtime

# Step 1: Run test coverage analysis
[[steps]]
id = "coverage"
description = "Run coverage analysis for task files"
command = """
pytest --cov=src \
  --cov-report=json:coverage-{{task_id}}.json \
  --cov-report=term
"""
output_file = "coverage-{{task_id}}.json"
timeout = 300  # 5 minutes max

# Step 2: Validate coverage threshold
[[steps]]
id = "check_coverage"
description = "Ensure coverage >= {{coverage_threshold}}%"
depends_on = ["coverage"]
command = """
COVERAGE=$(jq '.totals.percent_covered' coverage-{{task_id}}.json)
if (( $(echo "$COVERAGE >= {{coverage_threshold}}" | bc -l) )); then
  echo "PASS: Coverage ${COVERAGE}% >= {{coverage_threshold}}%"
  exit 0
else
  echo "FAIL: Coverage ${COVERAGE}% < {{coverage_threshold}}%"
  exit 1
fi
"""

# Step 3: Run mutation testing
[[steps]]
id = "mutation_testing"
description = "Run mutation testing on task files"
depends_on = ["coverage"]
command = """
# Python example (mutmut)
mutmut run --paths-to-mutate=src/ --tests-dir=tests/ \
  > mutmut-{{task_id}}.txt 2>&1

# JavaScript example (Stryker)
# npx stryker run --mutate="src/**/*.js" > stryker-{{task_id}}.txt

mutmut results
"""
output_file = "mutmut-{{task_id}}.txt"
timeout = 600  # 10 minutes max

# Step 4: Validate mutation score
[[steps]]
id = "check_mutation_score"
description = "Ensure mutation score >= {{mutation_threshold}}%"
depends_on = ["mutation_testing"]
command = """
# Parse mutation results
KILLED=$(mutmut results | grep -oP 'Killed: \\K[0-9]+')
TOTAL=$(mutmut results | grep -oP 'Total: \\K[0-9]+')
SCORE=$(echo "scale=2; ($KILLED / $TOTAL) * 100" | bc)

if (( $(echo "$SCORE >= {{mutation_threshold}}" | bc -l) )); then
  echo "PASS: Mutation score ${SCORE}% >= {{mutation_threshold}}%"
  exit 0
else
  echo "FAIL: Mutation score ${SCORE}% < {{mutation_threshold}}%"
  exit 1
fi
"""

# Step 5: Check AC traceability (map tests to AC)
[[steps]]
id = "ac_traceability"
description = "Verify all AC have corresponding tests"
depends_on = ["coverage"]
command = """
python3 << 'EOF'
import json
import sys

# Load AC from Beads
task_id = "{{task_id}}"
ac_list = json.loads(subprocess.check_output(
    f"bd show {task_id} --field acceptance_criteria --json",
    shell=True
))

# Load test file and check for AC references
# (Tests should have comments like: # AC1, # AC2, etc.)
with open("tests/auth/login.test.ts") as f:
    test_content = f.read()

missing_ac = []
for ac in ac_list:
    ac_id = ac['id']
    if f"# {ac_id}" not in test_content and f"// {ac_id}" not in test_content:
        missing_ac.append(ac_id)

if missing_ac:
    print(f"FAIL: Missing tests for AC: {', '.join(missing_ac)}")
    sys.exit(1)
else:
    print("PASS: All AC have corresponding tests")
    sys.exit(0)
EOF
"""

# Step 6: Record results in Beads
[[steps]]
id = "record_results"
description = "Store validation results in Beads"
depends_on = ["check_coverage", "check_mutation_score", "ac_traceability"]
command = """
# Mark task as test-quality validated
bd update {{task_id}} \
  --test-coverage $(jq '.totals.percent_covered' coverage-{{task_id}}.json) \
  --mutation-score $(mutmut results | grep -oP 'Killed: \\K[0-9]+' | head -1) \
  --test-quality-validated true \
  --validated-at $(date -Iseconds) \
  --validated-by tester-001

echo "Test quality validation complete for {{task_id}}"
"""
```

### Formula Execution Workflow

**Tester agent runs formula:**

```bash
# Tester invokes formula for task T001
cd worktree-tester-1/
bd cook test-quality-check --var task_id=T001

# Beads executes steps sequentially:
# 1. Run coverage → coverage-T001.json
# 2. Check coverage >= 80% → PASS/FAIL
# 3. Run mutation testing → mutmut-T001.txt
# 4. Check mutation score >= 80% → PASS/FAIL
# 5. Check AC traceability → PASS/FAIL
# 6. Record results in Beads → test-quality-validated=true

# If ALL steps pass:
bd show T001 --field test-quality-validated
# Output: true

# CAB can now route T001 to InDocs
```

**On formula failure:**

```bash
# If any step fails (e.g., coverage only 65%)
bd cook test-quality-check --var task_id=T001
# Output: FAIL: Coverage 65% < 80%

# Beads records failure
bd show T001 --field test-quality-validated
# Output: false

bd show T001 --field test-quality-failure-reason
# Output: "Coverage 65% < 80%"

# CAB routes back to InProgress
bd update T001 --status InProgress --reason "Test quality failed: Coverage 65%"

# Notify Developer
bd create --type event --agent dev-001 --event REWORK_NEEDED \
  --payload '{"task":"T001","reason":"Coverage 65%"}'
```

---

## Validation Thresholds Summary

### Quality Metrics Table

| Metric | Threshold | Max Allowed | Validation Tool | Enforced By | Action on Failure |
|--------|-----------|-------------|-----------------|-------------|-------------------|
| **Test Coverage** | 80% | N/A | pytest --cov, istanbul | Tester (formula) | Route to InProgress |
| **Mutation Score** | 80% | N/A | mutmut, Stryker | Tester (formula) | Route to InProgress |
| **Cyclomatic Complexity** | 10 (flag) | 15 (block) | radon, lizard, complexity-report | CAB (automated) | Flag: Review; Block: Route to InProgress |
| **Critical CVEs** | 0 | 0 | Trivy, Snyk | Refinery (pre-merge) | Block merge |
| **High CVEs** | 0 | 0 | Trivy, Snyk | Refinery (pre-merge) | Block merge |
| **Medium CVEs** | 0 (strict) | 5 (with justification) | Trivy, Snyk | Refinery (pre-merge) | Flag for review |
| **Secrets Detected** | 0 | 0 | TruffleHog, GitLeaks | Refinery (pre-merge) | Block merge |
| **SAST Findings (Critical)** | 0 | 0 | Semgrep, Bandit | Refinery (pre-merge) | Block merge |
| **AC Satisfaction** | 100% | N/A | Beads AC checklist | Tester (manual) | Route to InProgress |

### Rationale for Thresholds

**Coverage & Mutation (80%):**
- Industry standard for high-quality codebases
- Balances rigor with development velocity
- Mutation score ensures tests actually catch bugs (not just coverage theater)

**Cyclomatic Complexity (10/15):**
- McCabe's original recommendation (≤10 for testability)
- Functions >10 require >10 test cases (complexity grows exponentially)
- Hard limit at 15 prevents unmaintainable code

**Security (Zero Tolerance):**
- Critical/High CVEs pose immediate risk (data breach, RCE, privilege escalation)
- No acceptable risk for production deployment
- Medium CVEs allowed with justification (e.g., isolated component, mitigated by controls)

**AC Satisfaction (100%):**
- Acceptance criteria define "done" by design
- Partial satisfaction = incomplete feature
- No negotiation on business requirements

---

## CAB Routing Rules with Quality Gates

### State Machine with Quality Checks

**CAB routes tasks through states with validation at each transition:**

```
ToDo → InProgress → InTests → InDocs → Done
  ↑         ↓          ↓         ↓
  └─────────┴──────────┴─────────┘
     (Rollback on quality failure)
```

### Routing Logic Pseudocode

```bash
#!/bin/bash
# cab.sh - Permanent CAB agent routing logic

while true; do
  # Poll Beads for routing requests
  EVENT=$(bd list --type event --agent cab --status pending --limit 1 --json)

  if [ -n "$EVENT" ]; then
    EVENT_ID=$(echo $EVENT | jq -r '.id')
    TASK_ID=$(echo $EVENT | jq -r '.payload.task_id')
    FROM_STATE=$(echo $EVENT | jq -r '.payload.from')
    TO_STATE=$(echo $EVENT | jq -r '.payload.to')

    # Mark event as processing
    bd update $EVENT_ID --status processing

    # Route based on transition
    case "$FROM_STATE-$TO_STATE" in

      # InProgress → InTests (implementation complete, ready for testing)
      "InProgress-InTests")
        # Check: Code exists, compiles, basic tests pass
        if check_implementation_complete $TASK_ID; then
          bd update $TASK_ID --status InTests
          notify_tester $TASK_ID
        else
          bd update $TASK_ID --status InProgress --reason "Implementation incomplete"
        fi
        ;;

      # InTests → InDocs (tests pass, quality validated)
      "InTests-InDocs")
        # Check: Test quality formula passed
        TEST_QUALITY=$(bd show $TASK_ID --field test-quality-validated)
        AC_SATISFIED=$(bd ac-status $TASK_ID --json | jq -r '.percentage')

        if [ "$TEST_QUALITY" = "true" ] && [ "$AC_SATISFIED" -eq 100 ]; then
          bd update $TASK_ID --status InDocs
          notify_refinery $TASK_ID  # Ready for merge review
        else
          REASON="Test quality: $TEST_QUALITY, AC: ${AC_SATISFIED}%"
          bd update $TASK_ID --status InProgress --reason "$REASON"
          notify_developer $TASK_ID "Rework needed: $REASON"
        fi
        ;;

      # InDocs → Done (merged, documented, security validated)
      "InDocs-Done")
        # Check: Security scan passed, complexity acceptable, merged
        SECURITY_VALIDATED=$(bd show $TASK_ID --field security-validated)
        COMPLEXITY_OK=$(bd show $TASK_ID --field complexity-ok)
        MERGED=$(bd show $TASK_ID --field merged-to-main)

        if [ "$SECURITY_VALIDATED" = "true" ] && \
           [ "$COMPLEXITY_OK" = "true" ] && \
           [ "$MERGED" = "true" ]; then
          bd update $TASK_ID --status Done
          notify_librarian $TASK_ID  # Trigger doc update
        else
          REASON="Security: $SECURITY_VALIDATED, Complexity: $COMPLEXITY_OK, Merged: $MERGED"
          bd update $TASK_ID --status InProgress --reason "$REASON"
        fi
        ;;

      *)
        echo "Unknown transition: $FROM_STATE → $TO_STATE"
        ;;
    esac

    # Mark event as done
    bd close $EVENT_ID
  fi

  sleep 5  # Poll every 5 seconds (optimized from Topic 1: 30s)
done
```

### Quality Gate Functions (CAB Helpers)

```bash
check_implementation_complete() {
  TASK_ID=$1
  FILE=$(bd show $TASK_ID --field file)

  # Check file exists
  if [ ! -f "$FILE" ]; then
    return 1
  fi

  # Check basic tests exist (if test task)
  TEST_FILE=$(echo $FILE | sed 's|src/|tests/|' | sed 's|\.ts|.test.ts|')
  if [[ $TASK_ID == *"test"* ]] && [ ! -f "$TEST_FILE" ]; then
    return 1
  fi

  # Check code compiles (language-specific)
  # TypeScript: tsc --noEmit
  # Python: python -m py_compile $FILE

  return 0
}

notify_tester() {
  TASK_ID=$1
  bd create --type event --agent tester-001 --event RUN_TESTS \
    --payload "{\"task\":\"$TASK_ID\"}"
}

notify_refinery() {
  TASK_ID=$1
  bd create --type event --agent refinery --event SECURITY_SCAN \
    --payload "{\"task\":\"$TASK_ID\"}"
}

notify_developer() {
  TASK_ID=$1
  REASON=$2
  ASSIGNEE=$(bd show $TASK_ID --field assignee)
  bd create --type event --agent $ASSIGNEE --event REWORK_NEEDED \
    --payload "{\"task\":\"$TASK_ID\",\"reason\":\"$REASON\"}"
}

notify_librarian() {
  TASK_ID=$1
  CONVOY=$(bd show $TASK_ID --field story)
  bd create --type event --agent librarian --event UPDATE_DOCS \
    --payload "{\"convoy\":\"$CONVOY\",\"task\":\"$TASK_ID\"}"
}
```

---

## Security Validation: OWASP Top 10 2025 Compliance

### Required Security Scans (Pre-Merge)

**Refinery runs before merging to main:**

```bash
#!/bin/bash
# refinery.sh - Security validation before merge

validate_security() {
  TASK_ID=$1
  WORKTREE=$(bd show $TASK_ID --field worktree)

  cd $WORKTREE

  # 1. SAST (Static Application Security Testing)
  echo "Running SAST scan..."
  semgrep --config=auto --json src/ > sast-results-${TASK_ID}.json

  CRITICAL_SAST=$(jq '[.results[] | select(.extra.severity=="ERROR")] | length' sast-results-${TASK_ID}.json)

  if [ $CRITICAL_SAST -gt 0 ]; then
    echo "BLOCKED: $CRITICAL_SAST critical SAST findings"
    bd update $TASK_ID --security-validated false \
      --security-failure-reason "SAST: $CRITICAL_SAST critical findings"
    return 1
  fi

  # 2. Dependency Scan (CVE detection)
  echo "Running dependency scan..."
  trivy fs --severity CRITICAL,HIGH --format json src/ > trivy-results-${TASK_ID}.json

  CRITICAL_CVE=$(jq '[.Results[].Vulnerabilities[] | select(.Severity=="CRITICAL")] | length' trivy-results-${TASK_ID}.json)
  HIGH_CVE=$(jq '[.Results[].Vulnerabilities[] | select(.Severity=="HIGH")] | length' trivy-results-${TASK_ID}.json)

  if [ $CRITICAL_CVE -gt 0 ] || [ $HIGH_CVE -gt 0 ]; then
    echo "BLOCKED: $CRITICAL_CVE critical + $HIGH_CVE high CVEs"
    bd update $TASK_ID --security-validated false \
      --security-failure-reason "CVEs: $CRITICAL_CVE critical, $HIGH_CVE high"
    return 1
  fi

  # 3. Secret Detection
  echo "Running secret detection..."
  trufflehog filesystem src/ --json > secrets-${TASK_ID}.json

  SECRETS_FOUND=$(jq '. | length' secrets-${TASK_ID}.json)

  if [ $SECRETS_FOUND -gt 0 ]; then
    echo "BLOCKED: $SECRETS_FOUND secrets detected"
    bd update $TASK_ID --security-validated false \
      --security-failure-reason "Secrets: $SECRETS_FOUND found"
    return 1
  fi

  # 4. Cyclomatic Complexity Check
  echo "Checking cyclomatic complexity..."
  radon cc src/ -a -j > complexity-${TASK_ID}.json

  MAX_COMPLEXITY=$(jq '[.. | .complexity? // 0] | max' complexity-${TASK_ID}.json)

  if [ $MAX_COMPLEXITY -gt 15 ]; then
    echo "BLOCKED: Max complexity $MAX_COMPLEXITY > 15"
    bd update $TASK_ID --complexity-ok false \
      --complexity-max $MAX_COMPLEXITY
    return 1
  elif [ $MAX_COMPLEXITY -gt 10 ]; then
    echo "WARNING: Max complexity $MAX_COMPLEXITY (flagged for review)"
    bd update $TASK_ID --complexity-ok true --complexity-warning true \
      --complexity-max $MAX_COMPLEXITY
  else
    bd update $TASK_ID --complexity-ok true \
      --complexity-max $MAX_COMPLEXITY
  fi

  # All checks passed
  bd update $TASK_ID --security-validated true \
    --security-scanned-at $(date -Iseconds)

  echo "PASS: All security checks passed"
  return 0
}
```

### OWASP Top 10 2025 Mapping to Scans

| OWASP Category | Scan Type | Tool | What It Detects |
|----------------|-----------|------|-----------------|
| **A01: Broken Access Control** | SAST + DAST | Semgrep, OWASP ZAP | Missing auth checks, insecure direct object refs |
| **A02: Security Misconfiguration** | SAST + IaC | Semgrep, Checkov | Default credentials, verbose errors, exposed admin panels |
| **A03: Supply Chain Failures** | Dependency Scan | Trivy, Snyk | Vulnerable libraries, malicious packages |
| **A04: Cryptographic Failures** | SAST + Secret Detection | Semgrep, TruffleHog | Weak encryption, hardcoded keys, exposed credentials |
| **A05: Injection** | SAST + DAST | Semgrep, SQLMap | SQL injection, XSS, command injection |
| **A06: Insecure Design** | SAST | Semgrep | Missing rate limiting, lack of input validation |
| **A07: Vulnerable Components** | Dependency Scan | Trivy, Snyk | Outdated libraries with CVEs |
| **A08: Auth Failures** | SAST | Semgrep | Weak session management, missing MFA |
| **A09: Data Integrity Failures** | SAST | Semgrep | Missing signature verification, insecure deserialization |
| **A10: Exception Handling** | SAST | Semgrep | Verbose error messages, unhandled exceptions |

---

## Integration with Topic 1 Infrastructure

### How Quality Gates Fit into Agent Workflow

**Developer (InProgress → InTests):**
1. Developer implements task in `worktree-dev-001/`
2. Developer writes tests, runs locally
3. Developer marks task ready: `bd update T001 --status ready-for-testing`
4. Manager creates event: `bd create --type event --agent cab --event ROUTE_TASK --payload '{"task":"T001","from":"InProgress","to":"InTests"}'`
5. CAB routes to InTests, notifies Tester

**Tester (InTests → InDocs):**
1. Tester receives event, claims task
2. Tester runs formula: `bd cook test-quality-check --var task_id=T001`
3. Formula validates: coverage >80%, mutation >80%, AC traceability
4. Tester marks AC satisfied: `bd ac-satisfy T001 AC1 AC2 AC3 AC4`
5. Tester marks ready: `bd update T001 --status ready-for-docs`
6. Manager creates event for CAB
7. CAB routes to InDocs, notifies Refinery

**Refinery (InDocs → Done):**
1. Refinery receives event, runs security validation
2. Refinery executes: `validate_security T001`
3. Scans: SAST + Dependency + Secrets + Complexity
4. If PASS: Refinery merges worktree to main
5. Refinery marks: `bd update T001 --merged-to-main true --security-validated true`
6. Refinery creates event for CAB
7. CAB routes to Done, notifies Librarian

**Librarian (Convoy Done):**
1. Librarian receives event when ALL tasks in convoy Done
2. Librarian generates As-Built documentation
3. Librarian marks convoy complete: `bd update convoy-us1 --status Done`

---

## Decisions Summary

| Decision Point | Choice | Rationale |
|----------------|--------|-----------|
| **AC Storage** | Beads metadata (Option C) | No duplication, queryable, traceable |
| **Test Quality** | Formula-based automation (Option A) | Repeatable, automated, consistent |
| **Mutation Score** | 80% threshold | Matches coverage, industry standard |
| **Cyclomatic Complexity** | Threshold: 10, Max: 15 | McCabe's recommendation, testability |
| **Security CVEs** | Zero critical/high, max 5 medium | Production safety, zero tolerance |
| **Required Scans** | SAST + Dependency + Secrets | OWASP Top 10 coverage |
| **Optional Scans** | DAST + IaC + Fuzzing | If time/resources permit |

---

## Next Steps

**Topic 2 is LOCKED.** Proceed to:

**Topic 3: Coordination & Recovery**
- Convoy allocation strategy (priority queuing)
- Merge strategy and load balancing
- Git hooks for failure recovery (GUPP clarification)
- Agent health monitoring
- Rollback and error handling

---

## References

### Test Quality
- Mutation Testing: https://en.wikipedia.org/wiki/Mutation_testing
- Python mutmut: https://pypi.org/project/mutmut/
- JavaScript Stryker: https://stryker-mutator.io/

### Code Quality
- Cyclomatic Complexity Best Practices: https://linearb.io/blog/cyclomatic-complexity
- McCabe's Original Paper: https://en.wikipedia.org/wiki/Cyclomatic_complexity
- Codacy Guide: https://blog.codacy.com/cyclomatic-complexity

### Security
- OWASP Top 10 2025: https://owasp.org/Top10/2025/
- GitLab OWASP Analysis: https://about.gitlab.com/blog/2025-owasp-top-10-whats-changed-and-why-it-matters/
- Aikido Developer Guide: https://www.aikido.dev/blog/owasp-top-10-2025-changes-for-developers
- Semgrep: https://semgrep.dev/
- Trivy: https://github.com/aquasecurity/trivy
- TruffleHog: https://github.com/trufflesecurity/trufflehog

### Integration
- Gas Town GitHub: https://github.com/steveyegge/gastown
- Beads Framework: User's existing installation
- Speckit Framework: `~/.claude/commands/speckit/`
