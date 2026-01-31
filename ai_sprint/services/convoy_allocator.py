"""Convoy allocation logic for distributing work to developers."""

import json
import sqlite3
from typing import Optional

from ai_sprint.services.state_manager import (
    get_convoy,
    get_db,
    list_convoys_by_feature,
    update_convoy_status,
)
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T055: FIFO convoy allocation
# =============================================================================

def allocate_next_convoy(
    conn: sqlite3.Connection,
    feature_id: str,
    agent_id: str,
) -> Optional[str]:
    """
    Allocate the next available convoy to an agent (FIFO order).

    Args:
        conn: Database connection
        feature_id: Feature identifier
        agent_id: Agent requesting work

    Returns:
        Convoy ID if allocated, None if no work available
    """
    # Get all available convoys for this feature
    convoys = list_convoys_by_feature(conn, feature_id, status="available")

    if not convoys:
        logger.debug(f"No available convoys for feature {feature_id}")
        return None

    # Sort by priority (P1, P2, P3) then creation time
    sorted_convoys = sorted(
        convoys,
        key=lambda c: (c["priority"], c["created_at"]),
    )

    # Take first available convoy
    convoy = sorted_convoys[0]
    convoy_id = convoy["id"]

    # Check dependencies before allocating
    if not check_convoy_dependencies_met(conn, convoy_id):
        logger.info(f"Convoy {convoy_id} dependencies not met - skipping")
        return None

    # Allocate convoy to agent
    update_convoy_status(conn, convoy_id, "in_progress", assignee=agent_id)

    logger.info(f"Allocated convoy {convoy_id} to agent {agent_id}")
    return convoy_id


# =============================================================================
# T056: Convoy dependency validation
# =============================================================================

def check_convoy_dependencies_met(
    conn: sqlite3.Connection,
    convoy_id: str,
) -> bool:
    """
    Check if all dependencies for a convoy are complete.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier

    Returns:
        True if all dependencies are done, False otherwise
    """
    convoy = get_convoy(conn, convoy_id)
    if not convoy:
        return False

    # Parse dependencies (JSON array)
    dependencies_str = convoy["dependencies"]
    if not dependencies_str:
        return True  # No dependencies

    dependencies = json.loads(dependencies_str)

    if not dependencies:
        return True  # Empty dependencies list

    # Check each dependency
    for dep_id in dependencies:
        dep_convoy = get_convoy(conn, dep_id)

        if not dep_convoy:
            logger.warning(f"Dependency convoy not found: {dep_id}")
            return False

        if dep_convoy["status"] != "done":
            logger.debug(
                f"Convoy {convoy_id} blocked by {dep_id} (status: {dep_convoy['status']})"
            )
            return False

    logger.debug(f"All dependencies met for convoy {convoy_id}")
    return True


def get_blocked_convoys(
    conn: sqlite3.Connection,
    feature_id: str,
) -> list[dict[str, str]]:
    """
    Get list of convoys blocked by dependencies.

    Args:
        conn: Database connection
        feature_id: Feature identifier

    Returns:
        List of dicts with keys: convoy_id, blocked_by (list of convoy IDs)
    """
    blocked = []

    convoys = list_convoys_by_feature(conn, feature_id, status="available")

    for convoy in convoys:
        convoy_id = convoy["id"]

        if not check_convoy_dependencies_met(conn, convoy_id):
            # Find which dependencies are blocking
            dependencies = json.loads(convoy["dependencies"] or "[]")
            blocking_deps = []

            for dep_id in dependencies:
                dep_convoy = get_convoy(conn, dep_id)
                if dep_convoy and dep_convoy["status"] != "done":
                    blocking_deps.append(dep_id)

            if blocking_deps:
                blocked.append({
                    "convoy_id": convoy_id,
                    "blocked_by": blocking_deps,
                })

    return blocked


def update_blocked_convoys_status(
    conn: sqlite3.Connection,
    feature_id: str,
) -> int:
    """
    Update status of convoys to 'blocked' if dependencies not met.

    Args:
        conn: Database connection
        feature_id: Feature identifier

    Returns:
        Number of convoys marked as blocked
    """
    count = 0

    convoys = list_convoys_by_feature(conn, feature_id, status="available")

    for convoy in convoys:
        convoy_id = convoy["id"]

        if not check_convoy_dependencies_met(conn, convoy_id):
            update_convoy_status(conn, convoy_id, "blocked")
            count += 1
            logger.info(f"Marked convoy {convoy_id} as blocked")

    return count


def unblock_dependent_convoys(
    conn: sqlite3.Connection,
    completed_convoy_id: str,
) -> int:
    """
    Unblock convoys that were waiting for this convoy to complete.

    Args:
        conn: Database connection
        completed_convoy_id: Convoy that just completed

    Returns:
        Number of convoys unblocked
    """
    count = 0

    # Get convoy's feature
    completed_convoy = get_convoy(conn, completed_convoy_id)
    if not completed_convoy:
        return 0

    feature_id = completed_convoy["feature_id"]

    # Find all blocked convoys in this feature
    blocked_convoys = list_convoys_by_feature(conn, feature_id, status="blocked")

    for convoy in blocked_convoys:
        convoy_id = convoy["id"]

        # Check if this convoy can now proceed
        if check_convoy_dependencies_met(conn, convoy_id):
            update_convoy_status(conn, convoy_id, "available")
            count += 1
            logger.info(f"Unblocked convoy {convoy_id}")

    return count
