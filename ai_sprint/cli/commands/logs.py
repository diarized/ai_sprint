"""Log viewing command for AI Sprint."""

import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import click
from rich.console import Console

from ai_sprint.utils.logging import get_logger, setup_logging

console = Console()


def get_log_file(agent: str | None = None) -> Path:
    """Get the path to the log file for an agent or main log.

    Args:
        agent: Agent name (e.g., 'developer', 'manager') or None for main log

    Returns:
        Path to log file
    """
    log_dir = Path.home() / ".ai-sprint" / "logs"

    if agent:
        # Agent-specific log (tmux session log)
        return log_dir / f"{agent}.log"
    else:
        # Main application log
        return log_dir / "ai-sprint.log"


def filter_logs_by_time(log_path: Path, since: str | None) -> list[str]:
    """Filter log lines by time.

    Args:
        log_path: Path to log file
        since: Time string (e.g., '1h', '30m', '2d')

    Returns:
        List of log lines within the time window
    """
    if not log_path.exists():
        return []

    # Parse since duration
    cutoff_time = None
    if since:
        try:
            # Parse duration: 5m, 1h, 2d
            value = int(since[:-1])
            unit = since[-1]

            if unit == "m":
                cutoff_time = datetime.now() - timedelta(minutes=value)
            elif unit == "h":
                cutoff_time = datetime.now() - timedelta(hours=value)
            elif unit == "d":
                cutoff_time = datetime.now() - timedelta(days=value)
            else:
                raise ValueError(f"Invalid time unit: {unit}")
        except (ValueError, IndexError) as e:
            raise ValueError(f"Invalid --since format: {since}. Use: 5m, 1h, 2d") from e

    # Read and filter lines
    with open(log_path) as f:
        lines = f.readlines()

    if not cutoff_time:
        return lines

    # Filter by timestamp (assumes log format has timestamp at start)
    filtered_lines = []
    for line in lines:
        try:
            # Try to parse timestamp from log line
            # Assuming format: "2026-01-31 10:30:45,123 - ..."
            timestamp_str = " ".join(line.split()[:2])
            log_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")

            if log_time >= cutoff_time:
                filtered_lines.append(line)
        except (ValueError, IndexError):
            # Can't parse timestamp, include line anyway
            filtered_lines.append(line)

    return filtered_lines


@click.command()
@click.argument("agent", required=False)
@click.option(
    "--tail",
    "-n",
    type=int,
    default=None,
    help="Show last N lines (like tail -n)",
)
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output (like tail -f)",
)
@click.option(
    "--since",
    type=str,
    help="Show logs since duration (e.g., 5m, 1h, 2d)",
)
@click.option(
    "--list",
    "list_agents",
    is_flag=True,
    help="List available agent logs",
)
def logs(
    agent: str | None,
    tail: int | None,
    follow: bool,
    since: str | None,
    list_agents: bool,
) -> None:
    """View AI Sprint logs.

    AGENT: Name of agent to view logs for (optional, shows main log if not specified)

    Examples:
        ai-sprint logs                  # View main application log
        ai-sprint logs manager          # View manager agent log
        ai-sprint logs --tail 50        # Last 50 lines
        ai-sprint logs --follow         # Follow log output
        ai-sprint logs --since 1h       # Last hour of logs
        ai-sprint logs --list           # List available logs
    """
    setup_logging()
    logger = get_logger(__name__)

    try:
        log_dir = Path.home() / ".ai-sprint" / "logs"

        # List available logs
        if list_agents:
            if not log_dir.exists():
                console.print("[yellow]⚠ Log directory does not exist[/yellow]")
                console.print(f"  Expected: {log_dir}")
                console.print("  Run: ai-sprint install")
                sys.exit(1)

            log_files = sorted(log_dir.glob("*.log"))

            if not log_files:
                console.print("[yellow]⚠ No log files found[/yellow]")
                console.print(f"  Directory: {log_dir}")
                return

            console.print("[bold cyan]Available Logs[/bold cyan]")
            console.print()

            for log_file in log_files:
                size = log_file.stat().st_size
                size_str = f"{size:,} bytes" if size < 1024 else f"{size/1024:.1f} KB"

                # Get last modified time
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                mtime_str = mtime.strftime("%Y-%m-%d %H:%M:%S")

                name = log_file.stem
                console.print(f"  [cyan]{name:20}[/cyan] {size_str:>15}  {mtime_str}")

            console.print()
            console.print("[dim]View log:[/dim] [cyan]ai-sprint logs <name>[/cyan]")
            return

        # Get log file path
        log_path = get_log_file(agent)

        if not log_path.exists():
            if agent:
                console.print(f"[yellow]⚠ Log file not found for agent: {agent}[/yellow]")
                console.print(f"  Expected: {log_path}")
                console.print()
                console.print("[dim]List available logs:[/dim] [cyan]ai-sprint logs --list[/cyan]")
            else:
                console.print("[yellow]⚠ Main log file not found[/yellow]")
                console.print(f"  Expected: {log_path}")
                console.print("  Run: ai-sprint install")

            sys.exit(1)

        # Follow mode (use tail -f)
        if follow:
            console.print(f"[dim]Following {log_path}...[/dim]")
            console.print(f"[dim]Press Ctrl+C to exit[/dim]")
            console.print()

            try:
                subprocess.run(["tail", "-f", str(log_path)])
            except KeyboardInterrupt:
                console.print()
                console.print("[dim]Stopped following log[/dim]")
                return

        # Read log content
        try:
            if since:
                lines = filter_logs_by_time(log_path, since)
            else:
                with open(log_path) as f:
                    lines = f.readlines()

            # Apply tail limit
            if tail and tail > 0:
                lines = lines[-tail:]

            # Display logs
            if agent:
                console.print(f"[bold cyan]Agent Log:[/bold cyan] {agent}")
            else:
                console.print("[bold cyan]Main Log[/bold cyan]")

            console.print(f"[dim]File: {log_path}[/dim]")
            console.print()

            if not lines:
                console.print("[yellow]⚠ No log entries found[/yellow]")
                if since:
                    console.print(f"  (within last {since})")
            else:
                for line in lines:
                    # Strip trailing newline, Rich will add it
                    console.print(line.rstrip())

                # Show summary
                console.print()
                console.print(f"[dim]Showing {len(lines)} lines[/dim]")

                if tail:
                    console.print(f"[dim]Use --tail <N> to show more/fewer lines[/dim]")
                if not follow:
                    console.print(f"[dim]Use --follow to stream new log entries[/dim]")

        except UnicodeDecodeError:
            console.print(f"[red]✗ Cannot read log file (encoding issue)[/red]")
            sys.exit(1)

        logger.info(f"Displayed logs{f' for {agent}' if agent else ''}")

    except ValueError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Failed to view logs:[/bold red] {e}")
        logger.error(f"Logs command failed: {e}", exc_info=True)
        sys.exit(1)
