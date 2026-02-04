# AI Sprint

Multi-agent orchestration system for autonomous software feature development from specification through to deployment.

## Overview

AI Sprint coordinates 9 specialized agent types (4 permanent infrastructure + 5 on-demand workers) using Git worktree isolation, SQLite-based state management, and multi-layer quality gates to autonomously implement software features with zero human intervention.

### Core Principles

- **Autonomous Execution**: Complete feature implementation from spec to merge without human intervention
- **Conflict Prevention**: Git worktree isolation ensures parallel development without merge conflicts
- **Quality Enforcement**: Multi-layer quality gates (linting, type checking, testing, mutation testing, SAST, CVE scanning)
- **Fault Tolerance**: Automatic crash recovery with state preservation
- **Observability**: Rich logging and tmux session inspection

## System Architecture

### Agent Types

**Permanent Infrastructure (4):**
- **Manager**: Orchestrates feature lifecycle, spawns workers, monitors health
- **CAB (Change Advisory Board)**: Routes reviews and approves merges
- **Refinery**: Handles merge operations to main branch
- **Librarian**: Generates and maintains documentation

**On-Demand Workers (5):**
- **Developer**: Implements code from specifications
- **Tester**: Writes tests and validates coverage
- **Linter**: Code quality and style enforcement
- **Security**: SAST and CVE scanning
- **Mutator**: Mutation testing for test quality

### Workflow

```
Specification → Task Parsing → Convoy Creation → Development → Testing →
Quality Gates → Review → Merge → Documentation → Deployment
```

## Quick Start

### Prerequisites

| Dependency | Minimum Version | Purpose |
|------------|----------------|---------|
| Python | 3.11+ | Runtime environment |
| Git | 2.20+ | Worktree support |
| tmux | 3.0+ | Session management |
| pip | Latest | Package installation |

### Installation

```bash
# Clone repository
git clone git@github.com:diarized/ai_sprint.git
cd ai_sprint

# Install in editable mode
pip install -e .

# Initialize system
ai-sprint install

# Verify installation
ai-sprint health
```

### Basic Usage

**CRITICAL:** You must run `ai-sprint start` from inside the Git repository you want to develop.

#### Step 1: Prepare Feature Specification

Create a feature directory with required files:

```bash
mkdir -p ~/feature-specs/my-feature
cd ~/feature-specs/my-feature

# spec.md - MUST contain feature name as first heading
echo "# My Feature Name" > spec.md

# plan.md and tasks.md - required to exist but never read (can be empty)
touch plan.md
touch tasks.md
```

**What AI Sprint actually reads:**
- `spec.md` - Extracts feature name from first `# heading`
- `plan.md` - Never read (existence checked only)
- `tasks.md` - Never read (parser not implemented, TODO)

#### Step 2: Start AI Sprint

Navigate to the repository you want to develop and start AI Sprint:

```bash
# Go to YOUR repository (NOT the AI Sprint repository)
cd ~/path/to/your/project

# Start AI Sprint with path to feature specs
ai-sprint start ~/feature-specs/my-feature
```

**Example:** To develop WebIMAP project:

```bash
cd ~/Scripts/Python/src/WebIMAP/src
ai-sprint start ~/feature-specs/webimap-feature
```

AI Sprint will:
- Use the current directory (`.`) as the Git repository
- Create worktrees in `./worktrees/` for isolated development
- Read specs from `~/feature-specs/webimap-feature/`
- Implement changes in your repository

#### Other Commands

```bash
# Check system status
ai-sprint status

# View logs
ai-sprint logs --tail 50

# Stop all agents
ai-sprint stop
```

## Documentation

- **[Installation Guide](docs/installation.md)**: Complete setup instructions for all platforms
- **[Architecture](docs/architecture.md)**: System design and agent interactions
- **[Configuration](docs/configuration.md)**: Configuration options and tuning

## Features

### Quality Gates

- **Linting**: ruff for code quality
- **Type Checking**: mypy for type safety
- **Testing**: pytest with coverage thresholds
- **Mutation Testing**: mutmut for test quality validation
- **SAST**: semgrep for security analysis
- **CVE Scanning**: trivy for dependency vulnerabilities

### Fault Tolerance

- Automatic agent restart on crash
- State preservation in SQLite
- Crash log collection
- Health monitoring and alerting

### Observability

- Structured logging to `~/.ai-sprint/logs/`
- tmux session inspection: `tmux attach -t ai-sprint-<agent>`
- Health checks: `ai-sprint health --json`
- Real-time status: `ai-sprint status`

## Configuration

Default configuration location: `~/.ai-sprint/ai-sprint.toml`

Key settings:
- Agent concurrency limits
- Quality gate thresholds
- Timeout configurations
- Model selection (Claude Haiku/Sonnet)

See [Configuration Guide](docs/configuration.md) for details.

## System Requirements

### Minimum

- Python 3.11+
- Git 2.20+ (worktree support)
- tmux 3.0+
- 4GB RAM
- 2 CPU cores

### Recommended

- Python 3.12+
- Git 2.40+
- tmux 3.3+
- 8GB RAM
- 4 CPU cores
- SSD storage

## Contributing

This project uses the Beads workflow tracking system. See `.beads/` directory for issue tracking.

## License

See [LICENSE](LICENSE) file for details.

## Support

- **GitHub Repository**: https://github.com/diarized/ai_sprint
- **Issues**: https://github.com/diarized/ai_sprint/issues
- **Documentation**: https://github.com/diarized/ai_sprint/tree/master/docs

## Project Status

Active development. See GitHub issues for roadmap and current work.
