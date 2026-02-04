# Installation Guide: AI Sprint

Complete installation instructions for AI Sprint system.

## System Requirements

### Required Dependencies

| Dependency | Minimum Version | Purpose |
|------------|----------------|---------|
| Python | 3.11+ | Runtime environment |
| Git | 2.20+ | Worktree support |
| tmux | 3.0+ | Session management |
| pip | Latest | Package installation |

### Optional Tools (Quality Gates)

| Tool | Purpose | Installation |
|------|---------|--------------|
| ruff | Code linting | `pip install ruff` |
| mypy | Type checking | `pip install mypy` |
| pytest | Testing framework | `pip install pytest pytest-cov` |
| semgrep | SAST scanning | `pip install semgrep` |
| trivy | CVE scanning | OS package manager |
| mutmut | Mutation testing | `pip install mutmut` |

---

## Installation Methods

### Method 1: pip (Recommended)

**For development/editable install:**

```bash
# Clone repository
git clone git@github.com:diarized/ai_sprint.git
cd ai_sprint

# Install in editable mode
pip install -e .

# Initialize system
ai-sprint install
```

**For production install (when published to PyPI):**

```bash
# Install from PyPI
pip install ai-sprint

# Initialize system
ai-sprint install
```

### Method 2: pipx (Isolated Environment)

```bash
# Install pipx if not already installed
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install AI Sprint
pipx install ai-sprint

# Initialize system
ai-sprint install
```

### Method 3: From Source (Development)

```bash
# Clone repository
git clone git@github.com:diarized/ai_sprint.git
cd ai_sprint

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Initialize system
ai-sprint install
```

---

## Pre-Installation Check

Run the dependency checker before installation:

```bash
# From the repository root
bash scripts/install.sh
```

This will:
- Check Python, Git, and tmux versions
- Verify pip availability
- List optional tools status
- Provide OS-specific installation commands for missing dependencies

---

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install required dependencies
sudo apt install -y python3.11 python3-pip git tmux

# Install optional tools
sudo apt install -y python3-venv
pip install ruff mypy pytest pytest-cov semgrep mutmut

# Install trivy (CVE scanner)
sudo apt install wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt update
sudo apt install trivy
```

### Fedora/RHEL/CentOS

```bash
# Install required dependencies
sudo dnf install -y python3.11 python3-pip git tmux

# Install optional tools
pip install ruff mypy pytest pytest-cov semgrep mutmut

# Install trivy
RELEASE_VERSION=$(grep -Po '(?<=VERSION_ID=")[0-9]' /etc/os-release)
cat << EOF | sudo tee /etc/yum.repos.d/trivy.repo
[trivy]
name=Trivy repository
baseurl=https://aquasecurity.github.io/trivy-repo/rpm/releases/$RELEASE_VERSION/\$basearch/
gpgcheck=0
enabled=1
EOF
sudo dnf install -y trivy
```

### macOS

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install required dependencies
brew install python@3.11 git tmux

# Install optional tools
pip3 install ruff mypy pytest pytest-cov semgrep mutmut
brew install trivy
```

### Arch Linux

```bash
# Install required dependencies
sudo pacman -S python git tmux

# Install optional tools
pip install ruff mypy pytest pytest-cov semgrep mutmut
yay -S trivy  # Or use another AUR helper
```

---

## Post-Installation Setup

### 1. Initialize AI Sprint

```bash
ai-sprint install
```

This will:
- Create `~/.ai-sprint/` directory
- Initialize SQLite database
- Create example configuration file
- Set up log directories
- Run dependency check

### 2. Verify Installation

```bash
# Check system health
ai-sprint health

# View configuration
ai-sprint config show
```

### 3. Configure (Optional)

Edit configuration file:

```bash
# View current config
ai-sprint config show

# Edit specific settings
ai-sprint config set agents.max_developers 5
ai-sprint config set quality.coverage_threshold 85

# Or edit directly
nano ~/.ai-sprint/ai-sprint.toml
```

---

## Configuration File Structure

Default location: `~/.ai-sprint/ai-sprint.toml`

```toml
[general]
database_path = "~/.ai-sprint/beads.db"
log_level = "INFO"
log_file = "~/.ai-sprint/logs/ai-sprint.log"

[agents]
max_developers = 3
max_testers = 3
polling_interval_seconds = 30

[timeouts]
agent_heartbeat_seconds = 60
agent_hung_seconds = 300
task_max_duration_seconds = 7200
merge_timeout_seconds = 300

[quality]
coverage_threshold = 80
mutation_threshold = 80
complexity_flag = 10
complexity_max = 15

[security]
critical_cve_max = 0
high_cve_max = 0
medium_cve_max = 5

[models]
manager = "haiku"
cab = "haiku"
refinery = "sonnet"
librarian = "sonnet"
developer = "sonnet"
tester = "haiku"
```

---

## Troubleshooting

### Python Version Issues

```bash
# Check Python version
python3 --version

# If version is too old, install newer Python
# Ubuntu/Debian:
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev

# Update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Git Worktree Not Supported

```bash
# Check Git version
git --version

# Upgrade Git (Ubuntu/Debian)
sudo add-apt-repository ppa:git-core/ppa
sudo apt update
sudo apt install git
```

### tmux Not Available

```bash
# Install tmux
# Ubuntu/Debian:
sudo apt install tmux

# macOS:
brew install tmux

# Fedora/RHEL:
sudo dnf install tmux
```

### Permission Errors

```bash
# If pip installation fails due to permissions
pip install --user ai-sprint

# Or use virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install ai-sprint
```

### Database Lock Errors

```bash
# Check if another instance is running
ps aux | grep ai-sprint

# If database is locked, stop all instances
ai-sprint stop --force

# Remove lock file if needed
rm ~/.ai-sprint/beads.db-journal
```

---

## Uninstallation

### Remove AI Sprint Package

```bash
# If installed with pip
pip uninstall ai-sprint

# If installed with pipx
pipx uninstall ai-sprint
```

### Remove Configuration and Data

```bash
# WARNING: This will delete all data, features, and logs

# Backup first (optional)
tar -czf ai-sprint-backup-$(date +%Y%m%d).tar.gz ~/.ai-sprint

# Remove configuration directory
rm -rf ~/.ai-sprint
```

---

## Next Steps

After installation:

1. **Read the quickstart guide**: `docs/installation.md`
2. **Understand the architecture**: `docs/architecture.md`
3. **Learn configuration options**: `docs/configuration.md`
4. **Start your first feature**: `ai-sprint start <feature-dir>`

---

## Support

- **GitHub Repository**: https://github.com/diarized/ai_sprint
- **GitHub Issues**: https://github.com/diarized/ai_sprint/issues
- **Documentation**: https://github.com/diarized/ai_sprint/tree/master/docs
- **Health Check**: `ai-sprint health --json`
- **Logs**: `ai-sprint logs --tail 50`
