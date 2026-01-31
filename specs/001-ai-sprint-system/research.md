# Research: AI Sprint System

**Branch**: `001-ai-sprint-system` | **Date**: 2026-01-25
**Purpose**: Technology decisions and rationale for implementation

---

## Technology Decisions

### 1. CLI Framework: Click

**Decision**: Use Click for CLI interface

**Rationale**:
- Mature, well-documented library
- Declarative command definition
- Built-in help generation
- Supports nested command groups (ai-sprint start, ai-sprint status, etc.)
- Easy testing with CliRunner

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| argparse | Standard library | Verbose, less intuitive | More boilerplate for complex CLIs |
| Typer | Modern, type hints | Depends on Click anyway | Extra dependency for same functionality |
| Fire | Auto-generates CLI | Less control over UX | Limited customization |

---

### 2. Database: Raw SQLite (sqlite3)

**Decision**: Use Python's built-in sqlite3 module with helper functions

**Rationale**:
- Zero external dependencies (standard library)
- Direct control over SQL queries
- Simpler debugging (visible SQL)
- Sufficient for single-machine orchestration
- Dataclasses for type safety on Python side

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| SQLAlchemy | Type-safe queries, migrations | Heavy dependency, overkill | Adds complexity without proportional benefit |
| Peewee | Simple ORM | Still a dependency | Raw SQL is simpler for this use case |
| TinyDB | Document-oriented | No SQL, limited queries | Need relational queries for convoy allocation |

**Schema Migration Strategy**:
- Version number in schema_version table
- Migration scripts in `migrations/` directory
- Run migrations on startup if version mismatch
- Simple pattern: check version → apply missing migrations

---

### 3. Git Operations: GitPython

**Decision**: Use GitPython for worktree management

**Rationale**:
- Pythonic interface to git commands
- Worktree support via `git.Repo.worktree`
- Exception handling for git errors
- No shell command injection risks

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| subprocess + git | Direct control | Shell injection risk, parsing output | Security and maintenance |
| pygit2 | libgit2 bindings | More complex setup | GitPython is simpler |
| dulwich | Pure Python | Limited git features | Worktree support unclear |

**Worktree Pattern**:
```python
# Creating isolated worktree
repo = git.Repo(".")
worktree_path = f"worktrees/dev-{agent_id}"
repo.git.worktree("add", worktree_path)

# Cleaning up
repo.git.worktree("remove", worktree_path)
```

---

### 4. Session Management: libtmux

**Decision**: Use libtmux for tmux session control

**Rationale**:
- Python bindings for tmux
- Object-oriented session/window/pane model
- Avoids shell command parsing
- Supports session capture for logging

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| subprocess + tmux | Direct control | Parsing output, error handling | Complex and fragile |
| pexpect | Interactive control | Overkill for session management | More complexity |
| screen | Alternative to tmux | Less features, older | tmux is modern standard |

**Session Pattern**:
```python
import libtmux

server = libtmux.Server()
session = server.new_session(session_name=f"dev-{agent_id}")
window = session.attached_window
pane = window.attached_pane
pane.send_keys(f"claude --model {model} --system-prompt {prompt}")
```

---

### 5. Configuration: Pydantic Settings

**Decision**: Use Pydantic with pydantic-settings for configuration

**Rationale**:
- Type validation at load time
- Environment variable support
- TOML file support
- Default values with override
- IDE autocomplete for settings

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| Plain TOML | Simple | No validation | Runtime errors on bad config |
| dataclasses | Standard library | No env var support | Pydantic is more feature-rich |
| dynaconf | Feature-rich | Complex | Pydantic is sufficient |

**Configuration Pattern**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_path: str = "~/.ai-sprint/beads.db"
    max_developers: int = 3
    coverage_threshold: int = 80

    class Config:
        env_prefix = "AI_SPRINT_"
        toml_file = "ai-sprint.toml"
```

---

### 6. Logging: Rich

**Decision**: Use Rich for terminal output and logging

**Rationale**:
- Beautiful terminal output
- Progress bars for long operations
- Tables for status display
- Consistent styling
- Logging handler integration

**Alternatives Considered**:

| Option | Pros | Cons | Rejected Because |
|--------|------|------|------------------|
| Plain logging | Standard library | Ugly output | Poor UX |
| Colorama | Simple colors | Limited features | Rich is more comprehensive |
| Loguru | Pretty logging | Not a full TUI | Rich covers more use cases |

---

### 7. Quality Tools Integration

**Decision**: Invoke quality tools via subprocess with result parsing

**Rationale**:
- Tools already exist and are maintained
- JSON output for machine parsing
- Configurable via their own config files
- Easy to add/remove tools

**Tool Versions (Current as of 2026-01)**:

| Tool | Version | Output Format |
|------|---------|---------------|
| ruff | 0.4.x | JSON (--format json) |
| mypy | 1.10.x | JSON (--output json) |
| pytest-cov | 5.x | JSON (coverage json) |
| mutmut | 2.5.x | Custom (mutmut results) |
| semgrep | 1.x | JSON (--json) |
| trivy | 0.50.x | JSON (--format json) |
| trufflehog | 3.x | JSON (--json) |
| radon | 6.x | JSON (-j) |

**Integration Pattern**:
```python
import subprocess
import json

def run_coverage(task_id: str) -> dict:
    result = subprocess.run(
        ["pytest", "--cov=src", "--cov-report=json"],
        capture_output=True,
        text=True
    )
    with open("coverage.json") as f:
        return json.load(f)
```

---

## Best Practices Research

### Multi-Agent Orchestration (Gas Town Pattern)

**Source**: https://github.com/steveyegge/gastown

**Key Patterns Adopted**:
1. **Mayor Pattern**: Single orchestrator (Manager) controls work distribution
2. **Witness Pattern**: Health monitoring with heartbeats
3. **Convoy Pattern**: Bundle related tasks for single agent
4. **Sequential Merge**: Avoid conflicts via single merge point

**Key Differences from Gas Town**:
- AI Sprint uses Claude Code, Gas Town uses custom agents
- AI Sprint uses SQLite, Gas Town uses Firebase
- AI Sprint targets single machine, Gas Town is distributed

---

### Git Worktree Best Practices

**Research Source**: Git documentation, GitHub best practices

**Adopted Patterns**:
1. **Named worktrees**: `worktrees/dev-001` instead of random paths
2. **Cleanup on completion**: Remove worktree when convoy done
3. **Shared objects**: Worktrees share .git for space efficiency
4. **Branch per worktree**: Each worktree on unique branch

**Example Structure**:
```
project/
├── .git/                    # Shared git database
├── worktrees/
│   ├── dev-001/             # Developer 1 worktree
│   ├── dev-002/             # Developer 2 worktree
│   └── dev-003/             # Developer 3 worktree
└── src/                     # Main working directory
```

---

### SQLite Concurrency Best Practices

**Research Source**: SQLite documentation, Python sqlite3 docs

**Adopted Patterns**:
1. **WAL mode**: Write-Ahead Logging for concurrent reads
2. **Busy timeout**: 30 second timeout for lock contention
3. **Immediate transactions**: For atomic claiming
4. **Connection per operation**: Short-lived connections, no pooling needed

**Configuration**:
```python
import sqlite3
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect(
        "beads.db",
        timeout=30.0,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row  # Dict-like access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()
```

---

### Claude API Best Practices

**Research Source**: Anthropic documentation, Claude Code docs

**Adopted Patterns**:
1. **System prompts**: Define agent role and context
2. **Token limits**: Monitor and manage token usage
3. **Retry logic**: Exponential backoff on rate limits
4. **Model selection**: Haiku for simple, Sonnet for complex

**Rate Limit Handling**:
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=60))
def call_claude(prompt: str, model: str = "sonnet"):
    # API call here
    pass
```

---

## Dependency Compatibility Matrix

| Package | Python 3.11 | Python 3.12 | Notes |
|---------|-------------|-------------|-------|
| click | ✅ | ✅ | Stable |
| gitpython | ✅ | ✅ | Stable |
| libtmux | ✅ | ✅ | Stable |
| pydantic | ✅ | ✅ | 2.0+ required |
| rich | ✅ | ✅ | Stable |
| pytest | ✅ | ✅ | Stable |
| sqlite3 | ✅ | ✅ | Standard library |

---

## Security Considerations

### Secret Management

**Decision**: Use environment variables for sensitive config

**Rationale**:
- ANTHROPIC_API_KEY via environment
- Database path can contain secrets (encryption key)
- No secrets in config files

### Subprocess Security

**Decision**: Use list-based subprocess calls, never shell=True

**Rationale**:
- Prevents command injection
- Explicit argument handling
- Easier to audit

**Pattern**:
```python
# GOOD
subprocess.run(["git", "worktree", "add", path])

# BAD - Never do this
subprocess.run(f"git worktree add {path}", shell=True)
```

---

## Installation Research

### System Dependencies

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get install -y python3.11 python3-pip git tmux
```

**macOS (Homebrew)**:
```bash
brew install python@3.11 git tmux
```

### Python Package Installation

**Recommended**: pipx for isolation

```bash
pipx install ai-sprint
```

**Alternative**: pip with venv

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install ai-sprint
```

---

## Conclusions

All technology decisions are stable and well-supported. No blocking issues identified. Proceed to Phase 1 design.
