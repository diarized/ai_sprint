"""Main CLI entry point for AI Sprint."""

import click

from ai_sprint import __version__
from ai_sprint.cli.commands.config import config
from ai_sprint.cli.commands.health import health
from ai_sprint.cli.commands.install import install
from ai_sprint.cli.commands.logs import logs
from ai_sprint.cli.commands.start import start
from ai_sprint.cli.commands.status import status
from ai_sprint.cli.commands.stop import stop


@click.group()
@click.version_option(version=__version__, prog_name="ai-sprint")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """
    AI Sprint: Multi-agent orchestration system for autonomous software development.

    AI Sprint coordinates multiple AI agents to implement features from specification
    through to merged, tested, documented code without human intervention.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)


# Register commands
cli.add_command(install)
cli.add_command(health)
cli.add_command(config)
cli.add_command(start)
cli.add_command(stop)
cli.add_command(status)
cli.add_command(logs)


if __name__ == "__main__":
    cli()
