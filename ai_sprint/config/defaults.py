"""Default threshold values for AI Sprint."""

# Agent limits
MAX_DEVELOPERS_DEFAULT = 3
MAX_TESTERS_DEFAULT = 3
MAX_AGENTS_TOTAL = 10  # 4 infrastructure + 3 developers + 3 testers

# Polling and timeouts (seconds)
POLLING_INTERVAL_DEFAULT = 30
AGENT_HEARTBEAT_DEFAULT = 60
AGENT_HUNG_TIMEOUT = 300  # 5 minutes
TASK_MAX_DURATION = 7200  # 2 hours
MERGE_TIMEOUT = 300  # 5 minutes

# Quality gate thresholds
COVERAGE_THRESHOLD = 80  # percent
MUTATION_THRESHOLD = 80  # percent
COMPLEXITY_FLAG = 10  # cyclomatic complexity
COMPLEXITY_MAX = 15  # cyclomatic complexity

# Security thresholds
CRITICAL_CVE_MAX = 0  # zero tolerance
HIGH_CVE_MAX = 0  # zero tolerance
MEDIUM_CVE_MAX = 5  # allowed with justification

# Model assignments
MODEL_MANAGER = "haiku"  # high-frequency, low-complexity
MODEL_CAB = "haiku"  # high-frequency, low-complexity
MODEL_REFINERY = "sonnet"  # medium complexity
MODEL_LIBRARIAN = "sonnet"  # medium complexity
MODEL_DEVELOPER = "sonnet"  # medium complexity
MODEL_TESTER = "haiku"  # high-frequency, low-complexity

# Database
DATABASE_PATH_DEFAULT = "~/.ai-sprint/beads.db"
LOG_FILE_DEFAULT = "~/.ai-sprint/logs/ai-sprint.log"
LOG_LEVEL_DEFAULT = "INFO"
