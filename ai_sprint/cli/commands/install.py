"""Installation and initialization command for AI Sprint."""

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from ai_sprint.config.settings import Settings
from ai_sprint.services.state_manager import get_db, initialize_database
from ai_sprint.utils.logging import get_logger, setup_logging

console = Console()


@click.command()
@click.option(
    "--config-dir",
    type=click.Path(),
    default=None,
    help="Custom config directory (default: ~/.ai-sprint)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Force re-initialization even if already initialized",
)
def install(config_dir: str | None, force: bool) -> None:
    """Initialize AI Sprint system (database, config directory)."""
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Determine config directory
        if config_dir:
            config_path = Path(config_dir).expanduser().resolve()
        else:
            config_path = Path.home() / ".ai-sprint"

        console.print("[bold cyan]AI Sprint Installation[/bold cyan]")
        console.print(f"Config directory: {config_path}")
        console.print()

        # Check if already initialized
        if config_path.exists() and not force:
            console.print(
                "[yellow]⚠ AI Sprint already initialized at this location.[/yellow]"
            )
            console.print(
                "  Use --force to re-initialize (will preserve existing database)"
            )
            console.print()

            # Show current status
            db_path = config_path / "beads.db"
            log_dir = config_path / "logs"

            console.print("[bold]Current status:[/bold]")
            console.print(f"  Database: {db_path} ({'exists' if db_path.exists() else 'missing'})")
            console.print(f"  Logs: {log_dir} ({'exists' if log_dir.exists() else 'missing'})")
            console.print()

            # Verify database can be opened
            if db_path.exists():
                try:
                    with get_db(str(db_path)) as conn:
                        cursor = conn.execute("SELECT COUNT(*) FROM features")
                        cursor.fetchone()
                    console.print("[green]✓ Database accessible[/green]")
                except Exception as e:
                    console.print(f"[red]✗ Database error: {e}[/red]")
                    sys.exit(1)

            console.print()
            console.print("[green]✓ Installation verified[/green]")
            console.print()
            console.print("Next steps:")
            console.print("  1. Run health check: ai-sprint health")
            console.print("  2. Start a feature: ai-sprint start <feature-dir>")
            return

        # Create config directory structure
        console.print("[bold]Creating directory structure...[/bold]")

        config_path.mkdir(parents=True, exist_ok=True)
        (config_path / "logs").mkdir(exist_ok=True)
        (config_path / "worktrees").mkdir(exist_ok=True)

        console.print(f"[green]✓ Created {config_path}[/green]")
        console.print(f"[green]✓ Created {config_path / 'logs'}[/green]")
        console.print(f"[green]✓ Created {config_path / 'worktrees'}[/green]")
        console.print()

        # Initialize database
        console.print("[bold]Initializing database...[/bold]")

        db_path = config_path / "beads.db"

        # Initialize database schema
        initialize_database(str(db_path))

        console.print(f"[green]✓ Database initialized at {db_path}[/green]")
        console.print()

        # Create example config if it doesn't exist
        config_file = config_path / "ai-sprint.toml"
        if not config_file.exists():
            console.print("[bold]Creating example configuration...[/bold]")

            example_config = """# AI Sprint Configuration
# Edit this file to customize system behavior

[general]
database_path = "{db_path}"
log_level = "INFO"
log_file = "{log_file}"

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
""".format(
                db_path=str(db_path),
                log_file=str(config_path / "logs" / "ai-sprint.log"),
            )

            config_file.write_text(example_config)
            console.print(f"[green]✓ Created config file at {config_file}[/green]")
            console.print()

        # Run dependency check
        console.print("[bold]Checking system dependencies...[/bold]")
        console.print()

        # Find install.sh script
        script_path = Path(__file__).parent.parent.parent.parent / "scripts" / "install.sh"

        if script_path.exists():
            result = subprocess.run(
                [str(script_path)],
                capture_output=False,
                text=True,
            )

            console.print()

            if result.returncode != 0:
                console.print(
                    "[yellow]⚠ Some dependencies are missing or outdated.[/yellow]"
                )
                console.print(
                    "  AI Sprint may not function correctly until these are resolved."
                )
                console.print()
        else:
            console.print(
                "[yellow]⚠ Dependency check script not found. Skipping.[/yellow]"
            )
            console.print()

        # Success summary
        console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
        console.print("[bold green]✓ Installation complete![/bold green]")
        console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
        console.print()
        console.print("[bold]Installation summary:[/bold]")
        console.print(f"  Config: {config_file}")
        console.print(f"  Database: {db_path}")
        console.print(f"  Logs: {config_path / 'logs'}")
        console.print()
        console.print("[bold]Next steps:[/bold]")
        console.print("  1. Run health check: [cyan]ai-sprint health[/cyan]")
        console.print("  2. Review config: [cyan]ai-sprint config show[/cyan]")
        console.print("  3. Start a feature: [cyan]ai-sprint start <feature-dir>[/cyan]")
        console.print()

        logger.info(f"AI Sprint initialized at {config_path}")

    except Exception as e:
        console.print(f"[bold red]✗ Installation failed:[/bold red] {e}")
        logger.error(f"Installation failed: {e}", exc_info=True)
        sys.exit(1)
