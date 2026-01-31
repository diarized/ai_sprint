"""Status command - display feature implementation status."""

import json
import time
from typing import Any, Optional

import click
from rich.console import Console
from rich.live import Live
from rich.table import Table

from ai_sprint.cli.utils import error
from ai_sprint.services.state_manager import (
    get_db,
    list_convoys_by_feature,
    list_features_by_status,
    list_tasks_by_convoy,
)
from ai_sprint.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)
console = Console()


# =============================================================================
# T048: ai-sprint status [--json] [--watch] command
# =============================================================================

@click.command()
@click.option(
    "--json-output",
    "--json",
    is_flag=True,
    help="Output status as JSON",
)
@click.option(
    "--watch",
    is_flag=True,
    help="Watch mode (refresh every 5 seconds)",
)
@click.option(
    "--db-path",
    default="~/.ai-sprint/beads.db",
    help="Path to database file",
)
@click.option(
    "--feature",
    help="Filter by specific feature ID",
)
def status(
    json_output: bool,
    watch: bool,
    db_path: str,
    feature: Optional[str],
) -> None:
    """
    Display AI Sprint implementation status.

    Example:
        ai-sprint status
        ai-sprint status --json
        ai-sprint status --watch
        ai-sprint status --feature 001-my-feature
    """
    setup_logging()

    try:
        if watch and not json_output:
            _watch_status(db_path, feature)
        else:
            _display_status(db_path, feature, json_output)

    except KeyboardInterrupt:
        console.print("\nStatus watch stopped")
    except Exception as e:
        error(f"Failed to get status: {e}")
        logger.exception("Status command failed")
        raise click.Abort()


def _display_status(
    db_path: str,
    feature_filter: Optional[str],
    json_output: bool,
) -> None:
    """
    Display current status.

    Args:
        db_path: Path to database
        feature_filter: Optional feature ID filter
        json_output: Output as JSON
    """
    with get_db(db_path) as conn:
        # Get all active features
        if feature_filter:
            features = [row for row in conn.execute(
                "SELECT * FROM features WHERE id = ?",
                (feature_filter,),
            ).fetchall()]
        else:
            features = conn.execute(
                "SELECT * FROM features WHERE status IN ('ready', 'in_progress') ORDER BY created_at"
            ).fetchall()

        if not features:
            if json_output:
                print(json.dumps({"features": []}))
            else:
                console.print("[yellow]No active features found[/yellow]")
            return

        # Build status data
        status_data = []
        for feature in features:
            feature_id = feature["id"]
            convoys = list_convoys_by_feature(conn, feature_id)

            convoy_data = []
            for convoy in convoys:
                convoy_id = convoy["id"]
                tasks = list_tasks_by_convoy(conn, convoy_id)

                task_counts = {
                    "total": len(tasks),
                    "todo": sum(1 for t in tasks if t["status"] == "todo"),
                    "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
                    "in_review": sum(1 for t in tasks if t["status"] == "in_review"),
                    "in_tests": sum(1 for t in tasks if t["status"] == "in_tests"),
                    "in_docs": sum(1 for t in tasks if t["status"] == "in_docs"),
                    "done": sum(1 for t in tasks if t["status"] == "done"),
                }

                convoy_data.append({
                    "id": convoy_id,
                    "story": convoy["story"],
                    "status": convoy["status"],
                    "assignee": convoy["assignee"],
                    "tasks": task_counts,
                })

            status_data.append({
                "id": feature_id,
                "name": feature["name"],
                "status": feature["status"],
                "convoys": convoy_data,
            })

        # Output
        if json_output:
            print(json.dumps({"features": status_data}, indent=2))
        else:
            _render_status_table(status_data)


def _render_status_table(status_data: list[dict[str, Any]]) -> None:
    """
    Render status as Rich table.

    Args:
        status_data: Status data structure
    """
    for feature_status in status_data:
        # Feature header
        console.print(f"\n[bold cyan]Feature:[/bold cyan] {feature_status['name']}")
        console.print(f"[dim]ID:[/dim] {feature_status['id']}")
        console.print(f"[dim]Status:[/dim] {feature_status['status']}")

        if not feature_status["convoys"]:
            console.print("[yellow]  No convoys created yet[/yellow]")
            continue

        # Convoys table
        table = Table(title="Convoys")
        table.add_column("Convoy", style="cyan")
        table.add_column("Story")
        table.add_column("Status", style="magenta")
        table.add_column("Assignee", style="green")
        table.add_column("Tasks", justify="right")

        for convoy in feature_status["convoys"]:
            tasks = convoy["tasks"]
            task_summary = (
                f"{tasks['done']}/{tasks['total']} done "
                f"({tasks['in_progress']} in progress)"
            )

            table.add_row(
                convoy["id"],
                convoy["story"],
                convoy["status"],
                convoy["assignee"] or "-",
                task_summary,
            )

        console.print(table)


def _watch_status(
    db_path: str,
    feature_filter: Optional[str],
) -> None:
    """
    Watch mode - refresh status every 5 seconds.

    Args:
        db_path: Path to database
        feature_filter: Optional feature ID filter
    """
    with Live(console=console, refresh_per_second=0.2) as live:
        while True:
            # Create renderable for current status
            with get_db(db_path) as conn:
                if feature_filter:
                    features = [row for row in conn.execute(
                        "SELECT * FROM features WHERE id = ?",
                        (feature_filter,),
                    ).fetchall()]
                else:
                    features = conn.execute(
                        "SELECT * FROM features WHERE status IN ('ready', 'in_progress') ORDER BY created_at"
                    ).fetchall()

                if not features:
                    live.update("[yellow]No active features found[/yellow]")
                    time.sleep(5)
                    continue

                # Build tables for all features
                renderables = []
                for feature in features:
                    feature_id = feature["id"]
                    convoys = list_convoys_by_feature(conn, feature_id)

                    table = Table(title=f"{feature['name']} ({feature_id})")
                    table.add_column("Convoy", style="cyan")
                    table.add_column("Status", style="magenta")
                    table.add_column("Tasks Done", justify="right")

                    for convoy in convoys:
                        tasks = list_tasks_by_convoy(conn, convoy["id"])
                        done_count = sum(1 for t in tasks if t["status"] == "done")
                        total_count = len(tasks)

                        table.add_row(
                            convoy["story"],
                            convoy["status"],
                            f"{done_count}/{total_count}",
                        )

                    renderables.append(table)

                # Update live display
                if renderables:
                    live.update(renderables[0] if len(renderables) == 1 else renderables[0])

            time.sleep(5)
