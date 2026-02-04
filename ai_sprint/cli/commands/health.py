"""Health check command for AI Sprint system."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ai_sprint.config.settings import Settings
from ai_sprint.services.state_manager import get_db
from ai_sprint.utils.logging import get_logger, setup_logging

console = Console()


def check_command_version(command: str, min_version: str | None = None) -> dict:
    """Check if a command exists and optionally verify minimum version.

    Returns:
        dict with keys: available (bool), version (str|None), meets_minimum (bool|None)
    """
    if not shutil.which(command):
        return {"available": False, "version": None, "meets_minimum": None}

    try:
        # Try to get version
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        version_output = result.stdout + result.stderr
        version = version_output.split()[1] if version_output else "unknown"

        # Simple version comparison if needed
        meets_minimum = None
        if min_version:
            try:
                # Basic version comparison (works for X.Y.Z format)
                current_parts = [int(x) for x in version.split(".")[:3]]
                min_parts = [int(x) for x in min_version.split(".")[:3]]
                meets_minimum = current_parts >= min_parts
            except (ValueError, IndexError):
                meets_minimum = None  # Can't determine

        return {
            "available": True,
            "version": version,
            "meets_minimum": meets_minimum,
        }

    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
        return {"available": True, "version": "unknown", "meets_minimum": None}


def check_python_packages(packages: list[str]) -> dict[str, dict]:
    """Check if Python packages are installed.

    Returns:
        dict mapping package name to {available: bool, version: str|None}
    """
    results = {}

    for package in packages:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "show", package],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # Parse version from output
                for line in result.stdout.splitlines():
                    if line.startswith("Version:"):
                        version = line.split(":", 1)[1].strip()
                        results[package] = {"available": True, "version": version}
                        break
                else:
                    results[package] = {"available": True, "version": "unknown"}
            else:
                results[package] = {"available": False, "version": None}

        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            results[package] = {"available": False, "version": None}

    return results


@click.command()
@click.option(
    "--fix",
    is_flag=True,
    help="Attempt to fix issues (install missing Python packages)",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output results as JSON",
)
def health(fix: bool, json_output: bool) -> None:
    """Check system health and dependency status."""
    setup_logging()
    logger = get_logger(__name__)

    try:
        health_data = {
            "system_deps": {},
            "python_packages": {},
            "optional_tools": {},
            "database": {},
            "overall_status": "healthy",
        }

        # Check system dependencies
        console.print("[bold cyan]System Dependencies[/bold cyan]")

        required_deps = {
            "python3": "3.11",
            "git": "2.20",
            "tmux": "3.0",
        }

        for cmd, min_ver in required_deps.items():
            info = check_command_version(cmd, min_ver)
            health_data["system_deps"][cmd] = info

            if not json_output:
                if info["available"]:
                    status = "✓" if info["meets_minimum"] != False else "⚠"
                    color = "green" if info["meets_minimum"] != False else "yellow"
                    console.print(
                        f"[{color}]{status}[/{color}] {cmd}: {info['version']} "
                        f"({'OK' if info['meets_minimum'] != False else f'need >= {min_ver}'})"
                    )
                else:
                    console.print(f"[red]✗[/red] {cmd}: not found (need >= {min_ver})")
                    health_data["overall_status"] = "unhealthy"

        if not json_output:
            console.print()

        # Check Python packages
        console.print("[bold cyan]Python Packages[/bold cyan]")

        required_packages = [
            "click",
            "gitpython",
            "libtmux",
            "pydantic",
            "pydantic-settings",
            "rich",
            "toml",
        ]

        pkg_info = check_python_packages(required_packages)
        health_data["python_packages"] = pkg_info

        missing_packages = []
        for pkg, info in pkg_info.items():
            if not json_output:
                if info["available"]:
                    console.print(f"[green]✓[/green] {pkg}: {info['version']}")
                else:
                    console.print(f"[red]✗[/red] {pkg}: not installed")
                    missing_packages.append(pkg)
                    health_data["overall_status"] = "unhealthy"

        if not json_output:
            console.print()

        # Attempt fix if requested
        if fix and missing_packages:
            console.print("[bold yellow]Attempting to install missing packages...[/bold yellow]")
            console.print()

            for pkg in missing_packages:
                console.print(f"Installing {pkg}...")
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", pkg],
                        check=True,
                        capture_output=True,
                    )
                    console.print(f"[green]✓ Installed {pkg}[/green]")
                except subprocess.CalledProcessError as e:
                    console.print(f"[red]✗ Failed to install {pkg}: {e}[/red]")

            console.print()

        # Check optional tools
        console.print("[bold cyan]Optional Tools[/bold cyan]")

        optional_tools = {
            "ruff": None,
            "mypy": None,
            "pytest": None,
            "semgrep": None,
            "trivy": None,
            "mutmut": None,
        }

        optional_count = 0
        for tool in optional_tools:
            info = check_command_version(tool)
            health_data["optional_tools"][tool] = info

            if not json_output:
                if info["available"]:
                    console.print(f"[green]✓[/green] {tool}: {info['version']}")
                    optional_count += 1
                else:
                    console.print(f"[yellow]⚠[/yellow] {tool}: not installed (optional)")

        if not json_output:
            console.print(f"\n[dim]Optional tools: {optional_count}/{len(optional_tools)} installed[/dim]")
            console.print()

        # Check database
        console.print("[bold cyan]Database[/bold cyan]")

        config_path = Path.home() / ".ai-sprint"
        db_path = config_path / "beads.db"

        if db_path.exists():
            try:
                # Try a simple query
                with get_db(str(db_path)) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM features")
                    feature_count = cursor.fetchone()[0]

                health_data["database"] = {
                    "accessible": True,
                    "path": str(db_path),
                    "feature_count": feature_count,
                }

                if not json_output:
                    console.print(f"[green]✓[/green] Database accessible: {db_path}")
                    console.print(f"  Features: {feature_count}")

            except Exception as e:
                health_data["database"] = {
                    "accessible": False,
                    "path": str(db_path),
                    "error": str(e),
                }
                health_data["overall_status"] = "degraded"

                if not json_output:
                    console.print(f"[red]✗[/red] Database error: {e}")
        else:
            health_data["database"] = {
                "accessible": False,
                "path": str(db_path),
                "error": "Database not initialized",
            }

            if not json_output:
                console.print(f"[yellow]⚠[/yellow] Database not initialized")
                console.print("  Run: ai-sprint install")

        if not json_output:
            console.print()

        # Output results
        if json_output:
            click.echo(json.dumps(health_data, indent=2))
        else:
            # Summary
            console.print("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold]")

            if health_data["overall_status"] == "healthy":
                console.print("[bold green]✓ System healthy[/bold green]")
            elif health_data["overall_status"] == "degraded":
                console.print("[bold yellow]⚠ System degraded (some issues detected)[/bold yellow]")
            else:
                console.print("[bold red]✗ System unhealthy (critical issues)[/bold red]")

            console.print("[bold]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold]")
            console.print()

            if health_data["overall_status"] != "healthy":
                console.print("[bold]Recommended actions:[/bold]")

                if any(not info["available"] for info in health_data["system_deps"].values()):
                    console.print("  • Install missing system dependencies")
                    console.print("    Run: [cyan]scripts/install.sh[/cyan]")

                if any(not info["available"] for info in health_data["python_packages"].values()):
                    console.print("  • Install missing Python packages")
                    console.print("    Run: [cyan]ai-sprint health --fix[/cyan]")

                if not health_data["database"].get("accessible"):
                    console.print("  • Initialize database")
                    console.print("    Run: [cyan]ai-sprint install[/cyan]")

                console.print()

        # Exit code based on health status
        if health_data["overall_status"] == "unhealthy":
            sys.exit(1)
        elif health_data["overall_status"] == "degraded":
            sys.exit(2)

        logger.info("Health check completed successfully")

    except Exception as e:
        if json_output:
            click.echo(json.dumps({"error": str(e)}, indent=2))
        else:
            console.print(f"[bold red]✗ Health check failed:[/bold red] {e}")

        logger.error(f"Health check failed: {e}", exc_info=True)
        sys.exit(1)
