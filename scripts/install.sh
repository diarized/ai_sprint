#!/usr/bin/env bash
# AI Sprint System Dependency Checker and Installer
# Validates system dependencies and guides installation

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Minimum versions
readonly MIN_PYTHON_VERSION="3.11"
readonly MIN_GIT_VERSION="2.20"
readonly MIN_TMUX_VERSION="3.0"

# Track failures
MISSING_DEPS=()
VERSION_ISSUES=()

# Helper functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "ℹ $1"
}

# Version comparison function
version_ge() {
    # Returns 0 if $1 >= $2, 1 otherwise
    # Uses sort -V for version comparison
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check Python version
check_python() {
    print_info "Checking Python installation..."

    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found"
        MISSING_DEPS+=("python3")
        return 1
    fi

    local python_version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')

    if version_ge "$python_version" "$MIN_PYTHON_VERSION"; then
        print_success "Python $python_version (>= $MIN_PYTHON_VERSION)"
    else
        print_error "Python $python_version found, need >= $MIN_PYTHON_VERSION"
        VERSION_ISSUES+=("python3: $python_version < $MIN_PYTHON_VERSION")
        return 1
    fi
}

# Check Git version
check_git() {
    print_info "Checking Git installation..."

    if ! command -v git &> /dev/null; then
        print_error "Git not found"
        MISSING_DEPS+=("git")
        return 1
    fi

    local git_version
    git_version=$(git --version 2>&1 | awk '{print $3}')

    if version_ge "$git_version" "$MIN_GIT_VERSION"; then
        print_success "Git $git_version (>= $MIN_GIT_VERSION)"
    else
        print_error "Git $git_version found, need >= $MIN_GIT_VERSION for worktree support"
        VERSION_ISSUES+=("git: $git_version < $MIN_GIT_VERSION")
        return 1
    fi
}

# Check tmux version
check_tmux() {
    print_info "Checking tmux installation..."

    if ! command -v tmux &> /dev/null; then
        print_error "tmux not found"
        MISSING_DEPS+=("tmux")
        return 1
    fi

    local tmux_version
    tmux_version=$(tmux -V 2>&1 | awk '{print $2}')

    if version_ge "$tmux_version" "$MIN_TMUX_VERSION"; then
        print_success "tmux $tmux_version (>= $MIN_TMUX_VERSION)"
    else
        print_error "tmux $tmux_version found, need >= $MIN_TMUX_VERSION"
        VERSION_ISSUES+=("tmux: $tmux_version < $MIN_TMUX_VERSION")
        return 1
    fi
}

# Check pip availability
check_pip() {
    print_info "Checking pip installation..."

    if ! python3 -m pip --version &> /dev/null; then
        print_error "pip not available via python3 -m pip"
        MISSING_DEPS+=("python3-pip")
        return 1
    fi

    print_success "pip available"
}

# Check optional tools
check_optional_tools() {
    echo ""
    print_info "Checking optional quality tools (can be installed later)..."

    local optional_found=0

    if command -v ruff &> /dev/null; then
        print_success "ruff (linting)"
        ((optional_found++))
    else
        print_warning "ruff not found (install: pip install ruff)"
    fi

    if command -v mypy &> /dev/null; then
        print_success "mypy (type checking)"
        ((optional_found++))
    else
        print_warning "mypy not found (install: pip install mypy)"
    fi

    if command -v pytest &> /dev/null; then
        print_success "pytest (testing)"
        ((optional_found++))
    else
        print_warning "pytest not found (install: pip install pytest pytest-cov)"
    fi

    if command -v semgrep &> /dev/null; then
        print_success "semgrep (SAST)"
        ((optional_found++))
    else
        print_warning "semgrep not found (install: pip install semgrep)"
    fi

    if command -v trivy &> /dev/null; then
        print_success "trivy (CVE scanning)"
        ((optional_found++))
    else
        print_warning "trivy not found (install via package manager)"
    fi

    if command -v mutmut &> /dev/null; then
        print_success "mutmut (mutation testing)"
        ((optional_found++))
    else
        print_warning "mutmut not found (install: pip install mutmut)"
    fi

    echo ""
    print_info "Optional tools: $optional_found/6 installed"
}

# Provide installation guidance
provide_guidance() {
    if [[ ${#MISSING_DEPS[@]} -eq 0 && ${#VERSION_ISSUES[@]} -eq 0 ]]; then
        return 0
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Installation Guidance"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
        echo ""
        echo "Missing dependencies:"
        printf '  - %s\n' "${MISSING_DEPS[@]}"
        echo ""

        # Detect OS and provide specific instructions
        if [[ -f /etc/os-release ]]; then
            source /etc/os-release
            case "$ID" in
                ubuntu|debian)
                    echo "Ubuntu/Debian installation:"
                    echo "  sudo apt update"
                    echo "  sudo apt install ${MISSING_DEPS[*]}"
                    ;;
                fedora|rhel|centos)
                    echo "Fedora/RHEL/CentOS installation:"
                    echo "  sudo dnf install ${MISSING_DEPS[*]}"
                    ;;
                arch|manjaro)
                    echo "Arch Linux installation:"
                    echo "  sudo pacman -S ${MISSING_DEPS[*]}"
                    ;;
                *)
                    echo "Please install: ${MISSING_DEPS[*]}"
                    ;;
            esac
        elif [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macOS installation (using Homebrew):"
            echo "  brew install ${MISSING_DEPS[*]}"
        fi
    fi

    if [[ ${#VERSION_ISSUES[@]} -gt 0 ]]; then
        echo ""
        echo "Version issues:"
        printf '  - %s\n' "${VERSION_ISSUES[@]}"
        echo ""
        echo "Please upgrade these packages using your system package manager."
    fi

    echo ""
}

# Main check function
main() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "AI Sprint System Dependency Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Run all checks
    check_python
    check_git
    check_tmux
    check_pip
    check_optional_tools

    # Provide guidance if needed
    provide_guidance

    # Final status
    echo ""
    if [[ ${#MISSING_DEPS[@]} -eq 0 && ${#VERSION_ISSUES[@]} -eq 0 ]]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_success "All required dependencies satisfied!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Next steps:"
        echo "  1. Install AI Sprint: pip install -e ."
        echo "  2. Initialize system: ai-sprint install"
        echo "  3. Check health: ai-sprint health"
        echo ""
        return 0
    else
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        print_error "Dependency check failed"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        return 1
    fi
}

# Run main
main "$@"
