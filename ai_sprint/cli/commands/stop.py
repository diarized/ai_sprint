"""Stop command - halt feature implementation."""

import click

from ai_sprint.cli.utils import error, info, success
from ai_sprint.services.session_manager import SessionManager
from ai_sprint.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


# =============================================================================
# T047: ai-sprint stop [--force] command
# =============================================================================

@click.command()
@click.option(
    "--force",
    is_flag=True,
    help="Force stop all agents immediately",
)
def stop(force: bool) -> None:
    """
    Stop AI Sprint and all running agents.

    Example:
        ai-sprint stop
        ai-sprint stop --force
    """
    setup_logging()
    logger.info("Stopping AI Sprint")

    try:
        session_manager = SessionManager()
        sessions = session_manager.list_sessions()

        # Filter AI Sprint sessions (manager, dev-*, test-*, etc.)
        ai_sprint_sessions = [
            s for s in sessions
            if s.startswith(("manager", "dev-", "test-", "cab", "refinery", "librarian"))
        ]

        if not ai_sprint_sessions:
            info("No active AI Sprint sessions found")
            return

        info(f"Found {len(ai_sprint_sessions)} active sessions:")
        for session_name in ai_sprint_sessions:
            info(f"  - {session_name}")

        if not force:
            if not click.confirm("\nStop all AI Sprint sessions?"):
                info("Stop cancelled")
                return

        # Stop all sessions
        stopped_count = 0
        for session_name in ai_sprint_sessions:
            try:
                session_manager.destroy_session(session_name)
                logger.info(f"Stopped session: {session_name}")
                stopped_count += 1
            except Exception as e:
                error(f"Failed to stop {session_name}: {e}")

        success(f"Stopped {stopped_count}/{len(ai_sprint_sessions)} sessions")

    except Exception as e:
        error(f"Failed to stop AI Sprint: {e}")
        logger.exception("Stop command failed")
        raise click.Abort()
