#!/usr/bin/env bash
# AI Sprint Quick Health Check
# Fast validation script for CI/CD and quick troubleshooting

set -euo pipefail

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m'

# Exit codes
readonly EXIT_SUCCESS=0
readonly EXIT_MISSING_DEPS=1
readonly EXIT_DB_ERROR=2
readonly EXIT_CONFIG_ERROR=3

print_header() {
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "AI Sprint Quick Health Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

check_command() {
    local cmd=$1
    local required=${2:-true}

    if command -v "$cmd" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $cmd: available"
        return 0
    else
        if [[ "$required" == "true" ]]; then
            echo -e "${RED}✗${NC} $cmd: MISSING (required)"
            return 1
        else
            echo -e "${YELLOW}⚠${NC} $cmd: not found (optional)"
            return 0
        fi
    fi
}

check_python_package() {
    local package=$1

    if python3 -m pip show "$package" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $package: installed"
        return 0
    else
        echo -e "${RED}✗${NC} $package: MISSING"
        return 1
    fi
}

main() {
    print_header

    local exit_code=$EXIT_SUCCESS

    # Check required system commands
    echo "System Dependencies:"
    check_command python3 || exit_code=$EXIT_MISSING_DEPS
    check_command git || exit_code=$EXIT_MISSING_DEPS
    check_command tmux || exit_code=$EXIT_MISSING_DEPS
    echo ""

    # Check Python packages
    echo "Python Packages:"
    check_command pip3 || exit_code=$EXIT_MISSING_DEPS

    if command -v pip3 &> /dev/null; then
        check_python_package click || exit_code=$EXIT_MISSING_DEPS
        check_python_package gitpython || exit_code=$EXIT_MISSING_DEPS
        check_python_package libtmux || exit_code=$EXIT_MISSING_DEPS
        check_python_package pydantic || exit_code=$EXIT_MISSING_DEPS
        check_python_package rich || exit_code=$EXIT_MISSING_DEPS
    fi
    echo ""

    # Check optional tools
    echo "Optional Tools:"
    check_command ruff false
    check_command mypy false
    check_command pytest false
    echo ""

    # Check AI Sprint installation
    echo "AI Sprint:"
    if command -v ai-sprint &> /dev/null; then
        echo -e "${GREEN}✓${NC} ai-sprint: command available"

        # Try to get version
        if ai-sprint --version &> /dev/null; then
            version=$(ai-sprint --version 2>&1 | awk '{print $NF}')
            echo "  Version: $version"
        fi
    else
        echo -e "${YELLOW}⚠${NC} ai-sprint: command not found"
        echo "  Install: pip install -e ."
    fi
    echo ""

    # Check database
    echo "Database:"
    db_path="$HOME/.ai-sprint/beads.db"

    if [[ -f "$db_path" ]]; then
        echo -e "${GREEN}✓${NC} Database exists: $db_path"

        # Try to query database
        if command -v sqlite3 &> /dev/null; then
            if sqlite3 "$db_path" "SELECT COUNT(*) FROM features" &> /dev/null; then
                feature_count=$(sqlite3 "$db_path" "SELECT COUNT(*) FROM features")
                echo "  Features: $feature_count"
            else
                echo -e "${RED}✗${NC} Database query failed"
                exit_code=$EXIT_DB_ERROR
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} Database not initialized"
        echo "  Run: ai-sprint install"
    fi
    echo ""

    # Check configuration
    echo "Configuration:"
    config_path="$HOME/.ai-sprint/ai-sprint.toml"

    if [[ -f "$config_path" ]]; then
        echo -e "${GREEN}✓${NC} Config exists: $config_path"

        # Validate TOML syntax
        if command -v python3 &> /dev/null; then
            if python3 -c "import toml; toml.load(open('$config_path'))" 2> /dev/null; then
                echo "  TOML syntax: valid"
            else
                echo -e "${RED}✗${NC} TOML syntax: INVALID"
                exit_code=$EXIT_CONFIG_ERROR
            fi
        fi
    else
        echo -e "${YELLOW}⚠${NC} Config not found"
        echo "  Run: ai-sprint install"
    fi
    echo ""

    # Summary
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ $exit_code -eq $EXIT_SUCCESS ]]; then
        echo -e "${GREEN}✓ Health check PASSED${NC}"
        echo "  System is ready for AI Sprint operations"
    elif [[ $exit_code -eq $EXIT_MISSING_DEPS ]]; then
        echo -e "${RED}✗ Health check FAILED: Missing dependencies${NC}"
        echo "  Run: scripts/install.sh"
    elif [[ $exit_code -eq $EXIT_DB_ERROR ]]; then
        echo -e "${RED}✗ Health check FAILED: Database error${NC}"
        echo "  Run: ai-sprint install"
    elif [[ $exit_code -eq $EXIT_CONFIG_ERROR ]]; then
        echo -e "${RED}✗ Health check FAILED: Configuration error${NC}"
        echo "  Run: ai-sprint config reset"
    fi

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Advanced diagnostics suggestion
    if [[ $exit_code -ne $EXIT_SUCCESS ]]; then
        echo "For detailed diagnostics, run: ai-sprint health"
        echo ""
    fi

    exit "$exit_code"
}

main "$@"
