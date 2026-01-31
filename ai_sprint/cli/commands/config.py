"""Configuration management commands for AI Sprint."""

import sys
from pathlib import Path

import click
import toml
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table

from ai_sprint.utils.logging import setup_logging

console = Console()


def get_config_path() -> Path:
    """Get the path to the AI Sprint configuration file."""
    return Path.home() / ".ai-sprint" / "ai-sprint.toml"


def load_config() -> dict:
    """Load the current configuration file.

    Returns:
        dict: Configuration data

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    config_path = get_config_path()

    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found at {config_path}. "
            "Run 'ai-sprint install' to create it."
        )

    try:
        return toml.load(config_path)
    except toml.TomlDecodeError as e:
        raise ValueError(f"Invalid TOML in config file: {e}")


def save_config(config: dict) -> None:
    """Save configuration to file.

    Args:
        config: Configuration dictionary to save
    """
    config_path = get_config_path()

    try:
        with open(config_path, "w") as f:
            toml.dump(config, f)
    except Exception as e:
        raise RuntimeError(f"Failed to save config: {e}")


@click.group()
def config() -> None:
    """Manage AI Sprint configuration."""
    pass


@config.command("show")
@click.option(
    "--section",
    type=str,
    help="Show only specific section (general, agents, timeouts, quality, security, models)",
)
def show(section: str | None) -> None:
    """Display current configuration."""
    logger = setup_logging()

    try:
        config_data = load_config()
        config_path = get_config_path()

        console.print(f"[bold cyan]Configuration:[/bold cyan] {config_path}")
        console.print()

        if section:
            # Show specific section
            if section not in config_data:
                console.print(f"[red]✗ Section '{section}' not found in configuration[/red]")
                console.print(f"Available sections: {', '.join(config_data.keys())}")
                sys.exit(1)

            section_data = {section: config_data[section]}
            toml_str = toml.dumps(section_data)
        else:
            # Show full config
            toml_str = toml.dumps(config_data)

        # Display with syntax highlighting
        syntax = Syntax(toml_str, "toml", theme="monokai", line_numbers=False)
        console.print(syntax)
        console.print()

        console.print("[dim]Edit config file:[/dim] [cyan]nano ~/.ai-sprint/ai-sprint.toml[/cyan]")
        console.print("[dim]Or use:[/dim] [cyan]ai-sprint config set <key> <value>[/cyan]")

        logger.info(f"Displayed configuration{f' section: {section}' if section else ''}")

    except FileNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Failed to show config:[/bold red] {e}")
        logger.error(f"Config show failed: {e}", exc_info=True)
        sys.exit(1)


@config.command("set")
@click.argument("key")
@click.argument("value")
def set_value(key: str, value: str) -> None:
    """Set a configuration value.

    KEY format: section.key (e.g., agents.max_developers)
    VALUE: The value to set (will be auto-converted to appropriate type)

    Examples:
        ai-sprint config set agents.max_developers 5
        ai-sprint config set quality.coverage_threshold 85
        ai-sprint config set models.developer sonnet
    """
    logger = setup_logging()

    try:
        # Parse key
        if "." not in key:
            console.print("[red]✗ Key must be in format: section.key[/red]")
            console.print("Example: agents.max_developers")
            sys.exit(1)

        section, setting = key.split(".", 1)

        # Load current config
        config_data = load_config()

        if section not in config_data:
            console.print(f"[red]✗ Section '{section}' not found in configuration[/red]")
            console.print(f"Available sections: {', '.join(config_data.keys())}")
            sys.exit(1)

        # Convert value to appropriate type
        converted_value: int | float | bool | str

        # Try to preserve type of existing value if it exists
        if setting in config_data[section]:
            existing_value = config_data[section][setting]

            if isinstance(existing_value, bool):
                # Boolean conversion
                if value.lower() in ("true", "yes", "1", "on"):
                    converted_value = True
                elif value.lower() in ("false", "no", "0", "off"):
                    converted_value = False
                else:
                    console.print(f"[red]✗ Invalid boolean value: {value}[/red]")
                    console.print("Use: true/false, yes/no, 1/0, on/off")
                    sys.exit(1)
            elif isinstance(existing_value, int):
                try:
                    converted_value = int(value)
                except ValueError:
                    console.print(f"[red]✗ Invalid integer value: {value}[/red]")
                    sys.exit(1)
            elif isinstance(existing_value, float):
                try:
                    converted_value = float(value)
                except ValueError:
                    console.print(f"[red]✗ Invalid float value: {value}[/red]")
                    sys.exit(1)
            else:
                # String
                converted_value = value
        else:
            # New value - try to infer type
            try:
                # Try int first
                converted_value = int(value)
            except ValueError:
                try:
                    # Try float
                    converted_value = float(value)
                except ValueError:
                    # Try bool
                    if value.lower() in ("true", "yes", "1", "on"):
                        converted_value = True
                    elif value.lower() in ("false", "no", "0", "off"):
                        converted_value = False
                    else:
                        # Default to string
                        converted_value = value

        # Update config
        old_value = config_data[section].get(setting, "<not set>")
        config_data[section][setting] = converted_value

        # Save
        save_config(config_data)

        console.print(f"[green]✓ Updated {section}.{setting}[/green]")
        console.print(f"  Old: {old_value}")
        console.print(f"  New: {converted_value}")
        console.print()
        console.print("[dim]View config:[/dim] [cyan]ai-sprint config show[/cyan]")

        logger.info(f"Configuration updated: {section}.{setting} = {converted_value}")

    except FileNotFoundError as e:
        console.print(f"[red]✗ {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ Failed to set config:[/bold red] {e}")
        logger.error(f"Config set failed: {e}", exc_info=True)
        sys.exit(1)


@config.command("reset")
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt",
)
def reset(confirm: bool) -> None:
    """Reset configuration to defaults.

    WARNING: This will overwrite your current configuration file.
    """
    logger = setup_logging()

    try:
        config_path = get_config_path()

        if not confirm:
            console.print("[bold yellow]⚠ Warning:[/bold yellow] This will reset your configuration to defaults.")
            console.print(f"Current config: {config_path}")
            console.print()

            if not click.confirm("Continue?"):
                console.print("Cancelled.")
                return

        # Default configuration
        default_config = """# AI Sprint Configuration
# Edit this file to customize system behavior

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
"""

        # Ensure config directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write default config
        config_path.write_text(default_config)

        console.print(f"[green]✓ Configuration reset to defaults[/green]")
        console.print(f"  Config file: {config_path}")
        console.print()
        console.print("[dim]View config:[/dim] [cyan]ai-sprint config show[/cyan]")
        console.print("[dim]Customize:[/dim] [cyan]ai-sprint config set <key> <value>[/cyan]")

        logger.info("Configuration reset to defaults")

    except Exception as e:
        console.print(f"[bold red]✗ Failed to reset config:[/bold red] {e}")
        logger.error(f"Config reset failed: {e}", exc_info=True)
        sys.exit(1)
