"""CLI utility functions."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

console = Console()


def error(message: str) -> None:
    """
    Print error message to stderr and exit.

    Args:
        message: Error message to display
    """
    console.print(f"[red]✗ Error:[/red] {message}", stderr=True)
    raise click.Abort()


def success(message: str) -> None:
    """
    Print success message.

    Args:
        message: Success message to display
    """
    console.print(f"[green]✓[/green] {message}")


def info(message: str) -> None:
    """
    Print info message.

    Args:
        message: Info message to display
    """
    console.print(message)


def validate_feature_dir(feature_dir: str) -> Path:
    """
    Validate feature directory contains required files.

    Args:
        feature_dir: Path to feature specs directory

    Returns:
        Validated Path object

    Raises:
        click.Abort: If validation fails
    """
    path = Path(feature_dir)

    if not path.exists():
        error(f"Feature directory not found: {feature_dir}")

    if not path.is_dir():
        error(f"Not a directory: {feature_dir}")

    # Check for required files
    required_files = ["spec.md", "plan.md", "tasks.md"]
    missing = [f for f in required_files if not (path / f).exists()]

    if missing:
        error(f"Missing required files in {feature_dir}: {', '.join(missing)}")

    return path


def create_status_table(title: str, columns: list[str]) -> Table:
    """
    Create Rich table for status display.

    Args:
        title: Table title
        columns: List of column names

    Returns:
        Configured Rich Table
    """
    table = Table(title=title, show_header=True, header_style="bold")

    for column in columns:
        table.add_column(column)

    return table


def confirm(message: str, default: Optional[bool] = None) -> bool:
    """
    Prompt user for confirmation.

    Args:
        message: Confirmation prompt message
        default: Default value if user presses Enter

    Returns:
        User's confirmation choice
    """
    return click.confirm(message, default=default)
