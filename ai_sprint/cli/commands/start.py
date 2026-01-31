"""Start command - begin feature implementation."""

from pathlib import Path
from typing import Optional

import click

from ai_sprint.cli.utils import error, info, success, validate_feature_dir
from ai_sprint.core.manager import ManagerAgent
from ai_sprint.services.state_manager import create_feature, get_db, initialize_database
from ai_sprint.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


# =============================================================================
# T045: ai-sprint start <feature-dir> command
# =============================================================================

@click.command()
@click.argument("feature_dir", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--db-path",
    default="~/.ai-sprint/beads.db",
    help="Path to database file",
)
@click.option(
    "--polling-interval",
    default=30,
    type=int,
    help="Feature polling interval in seconds",
)
@click.option(
    "--max-developers",
    default=3,
    type=int,
    help="Maximum concurrent developer agents",
)
@click.option(
    "--max-testers",
    default=3,
    type=int,
    help="Maximum concurrent tester agents",
)
def start(
    feature_dir: Path,
    db_path: str,
    polling_interval: int,
    max_developers: int,
    max_testers: int,
) -> None:
    """
    Start AI Sprint feature implementation.

    FEATURE_DIR must contain spec.md, plan.md, and tasks.md.

    Example:
        ai-sprint start specs/001-my-feature
    """
    setup_logging()
    logger.info(f"Starting AI Sprint for feature: {feature_dir}")

    try:
        # T046: Feature validation
        _validate_feature_directory(feature_dir)

        # Initialize database
        initialize_database(db_path)

        # Register feature
        feature_id = feature_dir.name
        _register_feature(db_path, feature_id, feature_dir)

        # Start Manager agent
        info(f"Starting Manager agent (polling every {polling_interval}s)...")
        manager = ManagerAgent(
            db_path=db_path,
            polling_interval=polling_interval,
            max_developers=max_developers,
            max_testers=max_testers,
        )

        success(f"AI Sprint started for feature: {feature_id}")
        info("Press Ctrl+C to stop")

        # Run Manager polling loop
        manager.start()

    except FileNotFoundError as e:
        error(f"Validation failed: {e}")
        raise click.Abort()
    except Exception as e:
        error(f"Failed to start AI Sprint: {e}")
        logger.exception("Start command failed")
        raise click.Abort()


# =============================================================================
# T046: Feature validation (spec.md, plan.md, tasks.md existence)
# =============================================================================

def _validate_feature_directory(feature_dir: Path) -> None:
    """
    Validate feature directory contains required files.

    Args:
        feature_dir: Path to feature directory

    Raises:
        FileNotFoundError: If required files are missing
    """
    required_files = ["spec.md", "plan.md", "tasks.md"]

    for filename in required_files:
        file_path = feature_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file missing: {filename}\n"
                f"Feature directory must contain: {', '.join(required_files)}"
            )

    logger.info(f"Feature directory validated: {feature_dir}")


def _register_feature(
    db_path: str,
    feature_id: str,
    feature_dir: Path,
) -> None:
    """
    Register feature in database.

    Args:
        db_path: Path to database
        feature_id: Feature identifier
        feature_dir: Path to feature directory
    """
    # Extract feature name from spec.md (first h1 heading)
    spec_file = feature_dir / "spec.md"
    feature_name = _extract_feature_name(spec_file)

    with get_db(db_path) as conn:
        # Check if feature already exists
        existing = conn.execute(
            "SELECT id FROM features WHERE id = ?",
            (feature_id,),
        ).fetchone()

        if existing:
            info(f"Feature '{feature_id}' already registered")
            return

        # Create feature record
        create_feature(
            conn,
            feature_id=feature_id,
            name=feature_name,
            spec_path=str(feature_dir.absolute()),
            status="ready",
        )

        logger.info(f"Feature registered: {feature_id}")


def _extract_feature_name(spec_file: Path) -> str:
    """
    Extract feature name from spec.md.

    Args:
        spec_file: Path to spec.md

    Returns:
        Feature name (first h1 heading or filename)
    """
    try:
        content = spec_file.read_text()
        for line in content.split("\n"):
            if line.startswith("# "):
                return line[2:].strip()
    except Exception:
        pass

    # Fallback to directory name
    return spec_file.parent.name
