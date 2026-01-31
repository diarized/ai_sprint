# Configuration Guide: AI Sprint

Complete guide to configuring AI Sprint system behavior.

## Configuration File Location

Default: `~/.ai-sprint/ai-sprint.toml`

Custom location can be specified via environment variable:
```bash
export AI_SPRINT_CONFIG=/path/to/custom/config.toml
```

---

## Configuration Management

### View Current Configuration

```bash
# View full configuration
ai-sprint config show

# View specific section
ai-sprint config show --section agents
ai-sprint config show --section quality
```

### Update Configuration

```bash
# Set individual values
ai-sprint config set agents.max_developers 5
ai-sprint config set quality.coverage_threshold 85
ai-sprint config set models.developer opus

# Reset to defaults
ai-sprint config reset --confirm
```

### Manual Editing

```bash
# Edit with your preferred editor
nano ~/.ai-sprint/ai-sprint.toml
vim ~/.ai-sprint/ai-sprint.toml

# Validate after editing
ai-sprint health
```

---

## Configuration Sections

### [general] - System-Wide Settings

Controls database location, logging, and general behavior.

```toml
[general]
database_path = "~/.ai-sprint/beads.db"
log_level = "INFO"
log_file = "~/.ai-sprint/logs/ai-sprint.log"
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `database_path` | string | `~/.ai-sprint/beads.db` | SQLite database location |
| `log_level` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | string | `~/.ai-sprint/logs/ai-sprint.log` | Main log file path |

**Recommendations:**
- Keep database on fast SSD for better performance
- Use `DEBUG` log level only for troubleshooting (generates large logs)
- Rotate logs periodically if running continuously

---

### [agents] - Agent Pool Configuration

Controls the number of concurrent agents and polling behavior.

```toml
[agents]
max_developers = 3
max_testers = 3
polling_interval_seconds = 30
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_developers` | int | `3` | Maximum concurrent developer agents |
| `max_testers` | int | `3` | Maximum concurrent tester agents |
| `polling_interval_seconds` | int | `30` | How often Manager polls for new work |

**Tuning Guidelines:**

**For resource-constrained systems:**
```toml
max_developers = 1
max_testers = 1
polling_interval_seconds = 60
```

**For high-performance systems:**
```toml
max_developers = 5
max_testers = 5
polling_interval_seconds = 15
```

**Considerations:**
- Each agent spawns a Claude API session (costs apply)
- More agents = faster feature completion but higher resource usage
- Polling too frequently wastes API calls; too infrequently increases latency

---

### [timeouts] - Health Monitoring Thresholds

Controls when agents are considered crashed, hung, or stuck.

```toml
[timeouts]
agent_heartbeat_seconds = 60
agent_hung_seconds = 300
task_max_duration_seconds = 7200
merge_timeout_seconds = 300
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `agent_heartbeat_seconds` | int | `60` | Expected heartbeat interval (crash detection) |
| `agent_hung_seconds` | int | `300` | No heartbeat → hung (5 min) |
| `task_max_duration_seconds` | int | `7200` | Maximum task duration (2 hours) |
| `merge_timeout_seconds` | int | `300` | Git merge operation timeout (5 min) |

**Tuning Guidelines:**

**For complex features (large codebases):**
```toml
task_max_duration_seconds = 14400  # 4 hours
merge_timeout_seconds = 600        # 10 minutes
```

**For simple features (microservices):**
```toml
task_max_duration_seconds = 3600   # 1 hour
merge_timeout_seconds = 120        # 2 minutes
```

**Warning:** Setting `agent_heartbeat_seconds` too low may cause false crash detections during heavy API rate limiting.

---

### [quality] - Quality Gate Thresholds

Controls when code passes quality gates.

```toml
[quality]
coverage_threshold = 80
mutation_threshold = 80
complexity_flag = 10
complexity_max = 15
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `coverage_threshold` | int | `80` | Minimum test coverage percentage |
| `mutation_threshold` | int | `80` | Minimum mutation test score |
| `complexity_flag` | int | `10` | Cyclomatic complexity warning threshold |
| `complexity_max` | int | `15` | Cyclomatic complexity rejection threshold |

**Common Presets:**

**Strict (production-grade):**
```toml
coverage_threshold = 90
mutation_threshold = 85
complexity_flag = 8
complexity_max = 12
```

**Relaxed (MVP/prototype):**
```toml
coverage_threshold = 70
mutation_threshold = 70
complexity_flag = 15
complexity_max = 20
```

**Balanced (recommended):**
```toml
coverage_threshold = 80
mutation_threshold = 80
complexity_flag = 10
complexity_max = 15
```

**Notes:**
- Coverage threshold applies to line coverage (not branch coverage)
- Mutation threshold based on mutmut score
- Complexity measured per function using radon

---

### [security] - Security Gate Thresholds

Controls acceptable risk levels for vulnerabilities.

```toml
[security]
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 5
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `critical_cve_max` | int | `0` | Maximum critical CVEs (CVSS 9.0-10.0) |
| `high_cve_max` | int | `0` | Maximum high CVEs (CVSS 7.0-8.9) |
| `medium_cve_max` | int | `5` | Maximum medium CVEs (CVSS 4.0-6.9) |

**Security Postures:**

**Zero-trust (financial/healthcare):**
```toml
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 0
```

**Balanced (most organizations):**
```toml
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 5
```

**Permissive (internal tools, MVP):**
```toml
critical_cve_max = 0
high_cve_max = 2
medium_cve_max = 10
```

**Notes:**
- CVE scanning via trivy (must be installed)
- Thresholds apply to direct dependencies only
- False positives should be triaged and added to allowlist

---

### [models] - AI Model Selection

Controls which Claude models each agent uses.

```toml
[models]
manager = "haiku"
cab = "haiku"
refinery = "sonnet"
librarian = "sonnet"
developer = "sonnet"
tester = "haiku"
```

| Agent | Default Model | Purpose | Recommended |
|-------|---------------|---------|-------------|
| `manager` | `haiku` | Task orchestration | haiku (fast) |
| `cab` | `haiku` | Code review routing | haiku (sufficient) |
| `refinery` | `sonnet` | Merge decisions | sonnet (accuracy) |
| `librarian` | `sonnet` | Documentation | sonnet (quality) |
| `developer` | `sonnet` | Implementation | sonnet/opus |
| `tester` | `haiku` | Test validation | haiku (sufficient) |

**Available Models:**
- `haiku`: Fast, low-cost, good for simple tasks
- `sonnet`: Balanced, recommended for most tasks
- `opus`: Highest quality, use for complex implementation

**Cost Optimization:**
```toml
# Minimize costs (slower, lower quality)
manager = "haiku"
cab = "haiku"
refinery = "haiku"
librarian = "haiku"
developer = "haiku"
tester = "haiku"
```

**Quality Optimization:**
```toml
# Maximize quality (expensive, highest accuracy)
manager = "haiku"      # Orchestration doesn't need opus
cab = "sonnet"
refinery = "sonnet"
librarian = "sonnet"
developer = "opus"     # Best implementation quality
tester = "sonnet"
```

**Balanced (Recommended):**
```toml
# Best cost/quality ratio
manager = "haiku"
cab = "haiku"
refinery = "sonnet"
librarian = "sonnet"
developer = "sonnet"
tester = "haiku"
```

---

## Environment Variables

AI Sprint supports environment variable overrides:

```bash
# Override config file location
export AI_SPRINT_CONFIG=/custom/path/config.toml

# Override database path
export AI_SPRINT_DATABASE=/custom/path/beads.db

# Override log level
export AI_SPRINT_LOG_LEVEL=DEBUG

# Override log file
export AI_SPRINT_LOG_FILE=/var/log/ai-sprint.log
```

**Priority:** Environment variables > Config file > Defaults

---

## Validation

### Check Configuration Validity

```bash
# Health check includes config validation
ai-sprint health

# View current effective config
ai-sprint config show
```

### Common Validation Errors

**Invalid type:**
```toml
# ERROR: max_developers must be integer
max_developers = "three"

# CORRECT:
max_developers = 3
```

**Out of range:**
```toml
# ERROR: coverage_threshold must be 0-100
coverage_threshold = 150

# CORRECT:
coverage_threshold = 80
```

**Invalid model:**
```toml
# ERROR: Unknown model
developer = "gpt-4"

# CORRECT:
developer = "opus"
```

---

## Performance Tuning

### High Throughput (Many Features Per Week)

```toml
[agents]
max_developers = 5
max_testers = 5
polling_interval_seconds = 15

[timeouts]
task_max_duration_seconds = 3600  # Fail fast

[quality]
coverage_threshold = 75  # Slightly lower for speed
mutation_threshold = 75

[models]
developer = "sonnet"  # Opus too slow for high volume
```

### High Quality (Critical Production Code)

```toml
[agents]
max_developers = 2  # Fewer agents, more focus
max_testers = 2

[quality]
coverage_threshold = 95
mutation_threshold = 90
complexity_max = 10

[security]
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 0

[models]
developer = "opus"
refinery = "opus"
librarian = "opus"
```

### Resource Constrained (Low-End Machine)

```toml
[agents]
max_developers = 1
max_testers = 1
polling_interval_seconds = 60

[timeouts]
task_max_duration_seconds = 14400  # Allow more time

[models]
# All haiku to minimize memory/API load
manager = "haiku"
cab = "haiku"
refinery = "haiku"
librarian = "haiku"
developer = "haiku"
tester = "haiku"
```

---

## Best Practices

### 1. Start Conservative, Tune Later

Begin with defaults, monitor performance, adjust based on:
- Feature completion time
- Quality gate failure rate
- API costs
- Resource utilization

### 2. Document Changes

Keep a changelog in comments:

```toml
[agents]
# Increased from 3 to 5 on 2026-01-31 (faster feature delivery needed)
max_developers = 5
```

### 3. Version Control

Commit your customized config to version control (non-sensitive parts):

```bash
# Copy config to project
cp ~/.ai-sprint/ai-sprint.toml config/ai-sprint.toml

# Add to git (excluding sensitive data)
git add config/ai-sprint.toml
```

### 4. Test Changes

After config changes:

```bash
# Verify health
ai-sprint health

# Test with small feature
ai-sprint start specs/test-feature/
```

---

## Troubleshooting

### Configuration Not Loading

```bash
# Check which config file is being used
ai-sprint config show | head -1

# Verify file exists
ls -l ~/.ai-sprint/ai-sprint.toml

# Check permissions
chmod 644 ~/.ai-sprint/ai-sprint.toml
```

### Changes Not Taking Effect

```bash
# Restart AI Sprint
ai-sprint stop
ai-sprint start <feature-dir>

# Verify current config
ai-sprint config show
```

### Invalid TOML Syntax

```bash
# Common errors:
# - Missing quotes around strings
# - Incorrect section headers
# - Invalid boolean values (use true/false, not yes/no)

# Validate TOML syntax online:
# https://www.toml-lint.com/

# Or use Python:
python3 -c "import toml; toml.load(open('~/.ai-sprint/ai-sprint.toml'))"
```

---

## See Also

- [Installation Guide](installation.md)
- [Architecture Overview](architecture.md)
- [Quickstart Guide](quickstart.md)
