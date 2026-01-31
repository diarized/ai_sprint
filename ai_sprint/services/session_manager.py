"""Session management with tmux integration."""

import libtmux
from pathlib import Path
from typing import Optional

from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T031: tmux session creation/destruction
# =============================================================================

class SessionManager:
    """Manage tmux sessions for AI Sprint agents."""

    def __init__(self, server: Optional[libtmux.Server] = None):
        """
        Initialize session manager.

        Args:
            server: tmux server instance (creates new if None)
        """
        self.server = server or libtmux.Server()

    def create_session(self, session_name: str, working_dir: Optional[str] = None) -> libtmux.Session:
        """
        Create a new tmux session for an agent.

        Args:
            session_name: Unique session name (e.g., "dev-001", "manager")
            working_dir: Optional working directory for the session

        Returns:
            Created tmux session

        Raises:
            ValueError: If session already exists
        """
        # Check if session already exists
        if self.server.has_session(session_name):
            raise ValueError(f"Session '{session_name}' already exists")

        logger.info(f"Creating tmux session: {session_name}")

        # Create session with optional working directory
        session = self.server.new_session(
            session_name=session_name,
            start_directory=working_dir,
            attach=False,  # Don't attach to session
        )

        return session

    def destroy_session(self, session_name: str) -> None:
        """
        Destroy a tmux session.

        Args:
            session_name: Session name to destroy

        Raises:
            ValueError: If session doesn't exist
        """
        session = self.server.find_where({"session_name": session_name})
        if not session:
            raise ValueError(f"Session '{session_name}' not found")

        logger.info(f"Destroying tmux session: {session_name}")
        session.kill_session()

    def get_session(self, session_name: str) -> Optional[libtmux.Session]:
        """
        Get existing tmux session by name.

        Args:
            session_name: Session name

        Returns:
            Session object or None if not found
        """
        return self.server.find_where({"session_name": session_name})

    def list_sessions(self) -> list[str]:
        """
        List all active tmux session names.

        Returns:
            List of session names
        """
        return [s.name for s in self.server.list_sessions()]


# =============================================================================
# T032: Agent spawning via tmux panes
# =============================================================================

def spawn_agent(
    session: libtmux.Session,
    agent_type: str,
    agent_id: str,
    command: str,
    working_dir: Optional[str] = None,
) -> libtmux.Pane:
    """
    Spawn an agent in a tmux pane.

    Args:
        session: tmux session
        agent_type: Agent type (developer, tester, etc.)
        agent_id: Unique agent identifier
        command: Command to execute in pane
        working_dir: Optional working directory

    Returns:
        Created pane
    """
    logger.info(f"Spawning {agent_type} agent: {agent_id}")

    # Get or create window
    window = session.attached_window
    if not window:
        window = session.new_window(attach=False)

    # Create new pane for agent
    pane = window.split_window(
        attach=False,
        start_directory=working_dir,
    )

    # Send command to pane
    pane.send_keys(command)

    return pane


def send_command_to_pane(
    pane: libtmux.Pane,
    command: str,
    suppress_history: bool = False,
) -> None:
    """
    Send a command to a tmux pane.

    Args:
        pane: Target pane
        command: Command to execute
        suppress_history: If True, prepend space to avoid shell history
    """
    if suppress_history:
        command = f" {command}"  # Leading space prevents history in most shells

    pane.send_keys(command)


def get_pane_content(
    pane: libtmux.Pane,
    start_line: int = -100,
) -> str:
    """
    Get content from a tmux pane.

    Args:
        pane: Target pane
        start_line: Starting line (negative = from end)

    Returns:
        Pane content as string
    """
    return pane.cmd("capture-pane", "-p", "-S", str(start_line)).stdout[0]


# =============================================================================
# T033: Session logging capture
# =============================================================================

def enable_pane_logging(
    pane: libtmux.Pane,
    log_file: Path,
) -> None:
    """
    Enable logging for a tmux pane.

    Args:
        pane: Target pane
        log_file: Path to log file
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Enabling pane logging to: {log_file}")

    # Start pipe-pane logging
    pane.cmd("pipe-pane", "-o", f"cat >> {log_file}")


def disable_pane_logging(pane: libtmux.Pane) -> None:
    """
    Disable logging for a tmux pane.

    Args:
        pane: Target pane
    """
    logger.info("Disabling pane logging")
    pane.cmd("pipe-pane")  # No arguments = disable


def get_pane_log_path(
    agent_id: str,
    log_dir: Path = Path("~/.ai-sprint/logs"),
) -> Path:
    """
    Get standardized log file path for an agent.

    Args:
        agent_id: Agent identifier
        log_dir: Base log directory

    Returns:
        Path to log file
    """
    expanded_dir = log_dir.expanduser()
    return expanded_dir / f"{agent_id}.log"


def capture_session_logs(
    session: libtmux.Session,
    output_dir: Path,
) -> dict[str, Path]:
    """
    Capture logs from all panes in a session.

    Args:
        session: tmux session
        output_dir: Directory to save logs

    Returns:
        Mapping of pane_id -> log_file_path
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log_files = {}

    for window in session.windows:
        for pane in window.panes:
            pane_id = pane.id
            log_file = output_dir / f"pane-{pane_id}.log"

            # Capture pane content
            content = get_pane_content(pane, start_line=-10000)  # Last 10k lines
            log_file.write_text(content)

            log_files[pane_id] = log_file
            logger.debug(f"Captured pane {pane_id} to {log_file}")

    return log_files
