"""State management with SQLite database."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Optional

from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# T012: Database connection helper with WAL mode
@contextmanager
def get_db(db_path: str = "~/.ai-sprint/beads.db") -> Generator[sqlite3.Connection, None, None]:
    """
    Get database connection with WAL mode and foreign keys enabled.

    Args:
        db_path: Path to SQLite database file

    Yields:
        Database connection with row factory set to sqlite3.Row
    """
    expanded_path = Path(db_path).expanduser()
    expanded_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(
        str(expanded_path),
        timeout=30.0,
        check_same_thread=False,
    )
    conn.row_factory = sqlite3.Row  # Dict-like access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    try:
        yield conn
    finally:
        conn.close()


# T013: Schema creation
SCHEMA_SQL = """
-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Features table
CREATE TABLE IF NOT EXISTS features (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    spec_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ready', 'in_progress', 'done', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Convoys table
CREATE TABLE IF NOT EXISTS convoys (
    id TEXT PRIMARY KEY,
    feature_id TEXT NOT NULL REFERENCES features(id),
    story TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'in_progress', 'done', 'blocked')),
    files TEXT NOT NULL,
    dependencies TEXT,
    assignee TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Tasks table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    convoy_id TEXT NOT NULL REFERENCES convoys(id),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    file_path TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('todo', 'in_progress', 'in_review', 'in_tests', 'in_docs', 'done')),
    priority TEXT NOT NULL,
    assignee TEXT,
    acceptance_criteria TEXT NOT NULL,
    validation_results TEXT,
    failure_reason TEXT,
    failure_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    started_at TEXT,
    completed_at TEXT
);

-- Events table (message queue)
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    processed_at TEXT
);

-- Agent sessions table
CREATE TABLE IF NOT EXISTS agent_sessions (
    agent_id TEXT PRIMARY KEY,
    agent_type TEXT NOT NULL CHECK (agent_type IN ('manager', 'cab', 'refinery', 'librarian', 'developer', 'tester')),
    convoy_id TEXT REFERENCES convoys(id),
    current_task TEXT REFERENCES tasks(id),
    worktree TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'crashed', 'hung', 'stuck')),
    last_heartbeat TEXT NOT NULL,
    started_at TEXT NOT NULL DEFAULT (datetime('now')),
    crashed_at TEXT
);
"""

# T015: Indexes for query optimization
INDEXES_SQL = """
-- Event queue optimization
CREATE INDEX IF NOT EXISTS idx_events_agent_pending ON events(agent_id, status) WHERE status = 'pending';

-- Convoy allocation
CREATE INDEX IF NOT EXISTS idx_convoys_feature_status ON convoys(feature_id, status);
CREATE INDEX IF NOT EXISTS idx_convoys_assignee ON convoys(assignee);

-- Task tracking
CREATE INDEX IF NOT EXISTS idx_tasks_convoy ON tasks(convoy_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);

-- Health monitoring
CREATE INDEX IF NOT EXISTS idx_agent_sessions_status ON agent_sessions(status);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_heartbeat ON agent_sessions(last_heartbeat);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    """
    Create database schema with tables and indexes.

    Args:
        conn: Database connection
    """
    conn.executescript(SCHEMA_SQL)
    conn.executescript(INDEXES_SQL)
    conn.commit()


# T014: Schema migration support
MIGRATIONS: dict[int, str] = {
    1: SCHEMA_SQL + INDEXES_SQL,
}


def get_current_version(conn: sqlite3.Connection) -> int:
    """
    Get current schema version from database.

    Args:
        conn: Database connection

    Returns:
        Current schema version, or 0 if schema_version table doesn't exist
    """
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] or 0
    except sqlite3.OperationalError:
        # schema_version table doesn't exist yet
        return 0


def migrate(conn: sqlite3.Connection) -> None:
    """
    Apply pending database migrations.

    Args:
        conn: Database connection
    """
    current = get_current_version(conn)
    for version in sorted(MIGRATIONS.keys()):
        if version > current:
            conn.executescript(MIGRATIONS[version])
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()


def initialize_database(db_path: str = "~/.ai-sprint/beads.db") -> None:
    """
    Initialize database with schema and migrations.

    Args:
        db_path: Path to SQLite database file
    """
    with get_db(db_path) as conn:
        migrate(conn)


# =============================================================================
# T027: Feature CRUD operations
# =============================================================================

def create_feature(
    conn: sqlite3.Connection,
    feature_id: str,
    name: str,
    spec_path: str,
    status: str = "ready",
) -> None:
    """
    Create a new feature record.

    Args:
        conn: Database connection
        feature_id: Unique feature identifier
        name: Human-readable feature name
        spec_path: Path to feature specification directory
        status: Initial status (default: ready)
    """
    conn.execute(
        """
        INSERT INTO features (id, name, spec_path, status)
        VALUES (?, ?, ?, ?)
        """,
        (feature_id, name, spec_path, status),
    )
    conn.commit()


def get_feature(conn: sqlite3.Connection, feature_id: str) -> Optional[sqlite3.Row]:
    """
    Get feature by ID.

    Args:
        conn: Database connection
        feature_id: Feature identifier

    Returns:
        Feature row or None if not found
    """
    return conn.execute(  # type: ignore[return-value]
        "SELECT * FROM features WHERE id = ?",
        (feature_id,),
    ).fetchone()


def update_feature_status(
    conn: sqlite3.Connection,
    feature_id: str,
    status: str,
) -> None:
    """
    Update feature status with timestamp.

    Args:
        conn: Database connection
        feature_id: Feature identifier
        status: New status (ready, in_progress, done, failed)
    """
    timestamp_field = None
    if status == "in_progress":
        timestamp_field = "started_at"
    elif status in ("done", "failed"):
        timestamp_field = "completed_at"

    if timestamp_field:
        conn.execute(
            f"""
            UPDATE features
            SET status = ?, {timestamp_field} = datetime('now')
            WHERE id = ?
            """,
            (status, feature_id),
        )
    else:
        conn.execute(
            "UPDATE features SET status = ? WHERE id = ?",
            (status, feature_id),
        )
    conn.commit()


def list_features_by_status(
    conn: sqlite3.Connection,
    status: str,
) -> list[sqlite3.Row]:
    """
    List all features with given status.

    Args:
        conn: Database connection
        status: Feature status to filter by

    Returns:
        List of feature rows
    """
    return conn.execute(
        "SELECT * FROM features WHERE status = ? ORDER BY created_at",
        (status,),
    ).fetchall()


# =============================================================================
# T028: Convoy CRUD operations
# =============================================================================

def create_convoy(
    conn: sqlite3.Connection,
    convoy_id: str,
    feature_id: str,
    story: str,
    priority: str,
    files: list[str],
    dependencies: Optional[list[str]] = None,
    status: str = "available",
) -> None:
    """
    Create a new convoy record.

    Args:
        conn: Database connection
        convoy_id: Unique convoy identifier
        feature_id: Parent feature ID
        story: User story name
        priority: Priority level (P1, P2, P3)
        files: List of file paths this convoy touches
        dependencies: List of convoy IDs that must complete first
        status: Initial status (default: available)
    """
    import json

    conn.execute(
        """
        INSERT INTO convoys (id, feature_id, story, priority, files, dependencies, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            convoy_id,
            feature_id,
            story,
            priority,
            json.dumps(files),
            json.dumps(dependencies or []),
            status,
        ),
    )
    conn.commit()


def get_convoy(conn: sqlite3.Connection, convoy_id: str) -> Optional[sqlite3.Row]:
    """
    Get convoy by ID.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier

    Returns:
        Convoy row or None if not found
    """
    return conn.execute(
        "SELECT * FROM convoys WHERE id = ?",
        (convoy_id,),
    ).fetchone()


def update_convoy_status(
    conn: sqlite3.Connection,
    convoy_id: str,
    status: str,
    assignee: Optional[str] = None,
) -> None:
    """
    Update convoy status with optional assignee and timestamp.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier
        status: New status (available, in_progress, done, blocked)
        assignee: Agent ID for in_progress status
    """
    timestamp_field = None
    if status == "in_progress":
        timestamp_field = "started_at"
    elif status == "done":
        timestamp_field = "completed_at"

    if timestamp_field:
        conn.execute(
            f"""
            UPDATE convoys
            SET status = ?, assignee = ?, {timestamp_field} = datetime('now')
            WHERE id = ?
            """,
            (status, assignee, convoy_id),
        )
    else:
        conn.execute(
            "UPDATE convoys SET status = ?, assignee = ? WHERE id = ?",
            (status, assignee, convoy_id),
        )
    conn.commit()


def list_convoys_by_feature(
    conn: sqlite3.Connection,
    feature_id: str,
    status: Optional[str] = None,
) -> list[sqlite3.Row]:
    """
    List all convoys for a feature, optionally filtered by status.

    Args:
        conn: Database connection
        feature_id: Feature identifier
        status: Optional status filter

    Returns:
        List of convoy rows
    """
    if status:
        return conn.execute(
            "SELECT * FROM convoys WHERE feature_id = ? AND status = ? ORDER BY priority",
            (feature_id, status),
        ).fetchall()
    else:
        return conn.execute(
            "SELECT * FROM convoys WHERE feature_id = ? ORDER BY priority",
            (feature_id,),
        ).fetchall()


# =============================================================================
# T029: Task CRUD operations with atomic claiming
# =============================================================================

def create_task(
    conn: sqlite3.Connection,
    task_id: str,
    convoy_id: str,
    title: str,
    description: str,
    file_path: str,
    priority: str,
    acceptance_criteria: list[dict[str, Any]],
    status: str = "todo",
) -> None:
    """
    Create a new task record.

    Args:
        conn: Database connection
        task_id: Unique task identifier
        convoy_id: Parent convoy ID
        title: Brief task description
        description: Full task description
        file_path: Primary file this task modifies
        priority: Priority level (inherited from convoy)
        acceptance_criteria: List of AC objects
        status: Initial status (default: todo)
    """
    import json

    conn.execute(
        """
        INSERT INTO tasks (
            id, convoy_id, title, description, file_path,
            status, priority, acceptance_criteria
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            convoy_id,
            title,
            description,
            file_path,
            status,
            priority,
            json.dumps(acceptance_criteria),
        ),
    )
    conn.commit()


def get_task(conn: sqlite3.Connection, task_id: str) -> Optional[sqlite3.Row]:
    """
    Get task by ID.

    Args:
        conn: Database connection
        task_id: Task identifier

    Returns:
        Task row or None if not found
    """
    return conn.execute(
        "SELECT * FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()


def claim_task_atomic(
    conn: sqlite3.Connection,
    task_id: str,
    assignee: str,
) -> bool:
    """
    Atomically claim a task for an agent (prevents race conditions).

    Uses IMMEDIATE transaction to lock the database during claim check.

    Args:
        conn: Database connection
        task_id: Task identifier
        assignee: Agent ID claiming the task

    Returns:
        True if claim succeeded, False if already claimed
    """
    # Start IMMEDIATE transaction for atomic claiming
    conn.execute("BEGIN IMMEDIATE")
    try:
        row = conn.execute(
            "SELECT status, assignee FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if not row:
            conn.rollback()
            return False

        # Only claim if status is todo and no assignee
        if row["status"] == "todo" and row["assignee"] is None:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'in_progress', assignee = ?, started_at = datetime('now')
                WHERE id = ?
                """,
                (assignee, task_id),
            )
            conn.commit()
            return True
        else:
            conn.rollback()
            return False
    except Exception:
        conn.rollback()
        raise


def update_task_status(
    conn: sqlite3.Connection,
    task_id: str,
    status: str,
    assignee: Optional[str] = None,
) -> None:
    """
    Update task status with timestamp.

    Args:
        conn: Database connection
        task_id: Task identifier
        status: New status (todo, in_progress, in_review, in_tests, in_docs, done)
        assignee: Optional assignee update
    """
    timestamp_field = None
    if status == "in_progress":
        timestamp_field = "started_at"
    elif status == "done":
        timestamp_field = "completed_at"

    if timestamp_field:
        if assignee:
            conn.execute(
                f"""
                UPDATE tasks
                SET status = ?, assignee = ?, {timestamp_field} = datetime('now')
                WHERE id = ?
                """,
                (status, assignee, task_id),
            )
        else:
            conn.execute(
                f"""
                UPDATE tasks
                SET status = ?, {timestamp_field} = datetime('now')
                WHERE id = ?
                """,
                (status, task_id),
            )
    else:
        if assignee:
            conn.execute(
                "UPDATE tasks SET status = ?, assignee = ? WHERE id = ?",
                (status, assignee, task_id),
            )
        else:
            conn.execute(
                "UPDATE tasks SET status = ? WHERE id = ?",
                (status, task_id),
            )
    conn.commit()


def update_task_validation_results(
    conn: sqlite3.Connection,
    task_id: str,
    validation_results: dict[str, Any],
) -> None:
    """
    Update task validation results (coverage, mutation, security).

    Args:
        conn: Database connection
        task_id: Task identifier
        validation_results: Validation results dictionary
    """
    import json

    conn.execute(
        "UPDATE tasks SET validation_results = ? WHERE id = ?",
        (json.dumps(validation_results), task_id),
    )
    conn.commit()


def increment_task_failure_count(
    conn: sqlite3.Connection,
    task_id: str,
    failure_reason: str,
) -> int:
    """
    Increment task failure count and set failure reason.

    Args:
        conn: Database connection
        task_id: Task identifier
        failure_reason: Why the task failed

    Returns:
        New failure count
    """
    conn.execute(
        """
        UPDATE tasks
        SET failure_count = failure_count + 1, failure_reason = ?
        WHERE id = ?
        """,
        (failure_reason, task_id),
    )
    conn.commit()

    row = conn.execute(
        "SELECT failure_count FROM tasks WHERE id = ?",
        (task_id,),
    ).fetchone()

    return row["failure_count"] if row else 0


def list_tasks_by_convoy(
    conn: sqlite3.Connection,
    convoy_id: str,
    status: Optional[str] = None,
) -> list[sqlite3.Row]:
    """
    List all tasks for a convoy, optionally filtered by status.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier
        status: Optional status filter

    Returns:
        List of task rows
    """
    if status:
        return conn.execute(
            "SELECT * FROM tasks WHERE convoy_id = ? AND status = ? ORDER BY created_at",
            (convoy_id, status),
        ).fetchall()
    else:
        return conn.execute(
            "SELECT * FROM tasks WHERE convoy_id = ? ORDER BY created_at",
            (convoy_id,),
        ).fetchall()


# =============================================================================
# T030: Event queue operations (publish, consume, ack)
# =============================================================================

def publish_event(
    conn: sqlite3.Connection,
    agent_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> str:
    """
    Publish a new event to the queue.

    Args:
        conn: Database connection
        agent_id: Target agent identifier
        event_type: Event type code (ROUTE_TASK, CLAIM_CONVOY, etc.)
        payload: Event-specific data

    Returns:
        Event ID (UUID)
    """
    import json
    import uuid

    event_id = str(uuid.uuid4())
    conn.execute(
        """
        INSERT INTO events (id, agent_id, event_type, payload, status)
        VALUES (?, ?, ?, ?, 'pending')
        """,
        (event_id, agent_id, event_type, json.dumps(payload)),
    )
    conn.commit()
    return event_id


def consume_events(
    conn: sqlite3.Connection,
    agent_id: str,
    limit: int = 10,
) -> list[sqlite3.Row]:
    """
    Consume pending events for an agent (mark as processing).

    Args:
        conn: Database connection
        agent_id: Agent identifier
        limit: Maximum events to consume

    Returns:
        List of event rows
    """
    # Atomically claim events
    conn.execute("BEGIN IMMEDIATE")
    try:
        events = conn.execute(
            """
            SELECT * FROM events
            WHERE agent_id = ? AND status = 'pending'
            ORDER BY created_at
            LIMIT ?
            """,
            (agent_id, limit),
        ).fetchall()

        if events:
            event_ids = [e["id"] for e in events]
            placeholders = ",".join("?" * len(event_ids))
            conn.execute(
                f"UPDATE events SET status = 'processing' WHERE id IN ({placeholders})",
                event_ids,
            )

        conn.commit()
        return events
    except Exception:
        conn.rollback()
        raise


def acknowledge_event(
    conn: sqlite3.Connection,
    event_id: str,
    success: bool = True,
) -> None:
    """
    Acknowledge event processing (mark as done or failed).

    Args:
        conn: Database connection
        event_id: Event identifier
        success: True for done, False for failed
    """
    status = "done" if success else "failed"
    conn.execute(
        """
        UPDATE events
        SET status = ?, processed_at = datetime('now')
        WHERE id = ?
        """,
        (status, event_id),
    )
    conn.commit()


def get_pending_event_count(
    conn: sqlite3.Connection,
    agent_id: str,
) -> int:
    """
    Get count of pending events for an agent.

    Args:
        conn: Database connection
        agent_id: Agent identifier

    Returns:
        Number of pending events
    """
    row = conn.execute(
        "SELECT COUNT(*) as count FROM events WHERE agent_id = ? AND status = 'pending'",
        (agent_id,),
    ).fetchone()
    return row["count"] if row else 0


# =============================================================================
# T041: Task state machine (todo -> in_progress -> in_review -> in_tests -> in_docs -> done)
# =============================================================================

VALID_TASK_TRANSITIONS: dict[str, list[str]] = {
    "todo": ["in_progress"],
    "in_progress": ["in_review", "todo"],  # Can go back to todo on rejection
    "in_review": ["in_tests", "in_progress"],  # CAB approval or rejection
    "in_tests": ["in_docs", "in_progress"],  # Tester approval or rejection
    "in_docs": ["done", "in_progress"],  # Refinery merge or rejection
    "done": [],  # Terminal state
}


def validate_task_transition(
    from_status: str,
    to_status: str,
) -> bool:
    """
    Validate task status transition according to state machine.

    Args:
        from_status: Current status
        to_status: Desired status

    Returns:
        True if transition is valid
    """
    return to_status in VALID_TASK_TRANSITIONS.get(from_status, [])


def transition_task_status(
    conn: sqlite3.Connection,
    task_id: str,
    to_status: str,
) -> bool:
    """
    Transition task status with validation.

    Args:
        conn: Database connection
        task_id: Task identifier
        to_status: Desired status

    Returns:
        True if transition succeeded, False if invalid
    """
    task = get_task(conn, task_id)
    if not task:
        logger.error(f"Task not found: {task_id}")
        return False

    from_status = task["status"]

    if not validate_task_transition(from_status, to_status):
        logger.error(
            f"Invalid task transition: {from_status} -> {to_status} for task {task_id}"
        )
        return False

    update_task_status(conn, task_id, to_status)
    logger.info(f"Task {task_id} transitioned: {from_status} -> {to_status}")
    return True


# =============================================================================
# T042: Task rejection with failure reason
# =============================================================================

def reject_task(
    conn: sqlite3.Connection,
    task_id: str,
    reason: str,
    rejecting_agent: str,
) -> None:
    """
    Reject a task and send back to developer.

    Args:
        conn: Database connection
        task_id: Task to reject
        reason: Specific rejection reason
        rejecting_agent: Agent rejecting (cab, tester, refinery)
    """
    task = get_task(conn, task_id)
    if not task:
        logger.error(f"Task not found: {task_id}")
        return

    # Increment failure count
    failure_count = increment_task_failure_count(conn, task_id, reason)

    # Transition back to in_progress
    transition_task_status(conn, task_id, "in_progress")

    logger.warning(
        f"Task {task_id} rejected by {rejecting_agent} (failure #{failure_count}): {reason}"
    )

    # Check if escalation needed (3+ failures)
    if failure_count >= 3:
        logger.error(f"Task {task_id} failed {failure_count} times - escalation needed")
        publish_event(
            conn,
            agent_id="manager",
            event_type="ESCALATE_TASK",
            payload={"task_id": task_id, "failure_count": failure_count},
        )


# =============================================================================
# T043: Convoy completion detection
# =============================================================================

def check_convoy_completion(
    conn: sqlite3.Connection,
    convoy_id: str,
) -> bool:
    """
    Check if all tasks in a convoy are complete.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier

    Returns:
        True if all tasks done, False otherwise
    """
    tasks = list_tasks_by_convoy(conn, convoy_id)

    if not tasks:
        return False

    all_done = all(task["status"] == "done" for task in tasks)

    if all_done:
        logger.info(f"Convoy {convoy_id} complete - all tasks done")
        update_convoy_status(conn, convoy_id, "done")

    return all_done


# =============================================================================
# T044: Feature completion detection and cleanup
# =============================================================================

def check_feature_completion(
    conn: sqlite3.Connection,
    feature_id: str,
) -> bool:
    """
    Check if all convoys in a feature are complete.

    Args:
        conn: Database connection
        feature_id: Feature identifier

    Returns:
        True if all convoys done, False otherwise
    """
    convoys = list_convoys_by_feature(conn, feature_id)

    if not convoys:
        return False

    all_done = all(convoy["status"] == "done" for convoy in convoys)

    if all_done:
        logger.info(f"Feature {feature_id} complete - all convoys done")
        update_feature_status(conn, feature_id, "done")

    return all_done


def cleanup_feature(
    conn: sqlite3.Connection,
    feature_id: str,
) -> None:
    """
    Cleanup resources after feature completion.

    Args:
        conn: Database connection
        feature_id: Feature identifier
    """
    logger.info(f"Cleaning up feature: {feature_id}")

    # Mark feature as done if not already
    feature = get_feature(conn, feature_id)
    if feature and feature["status"] != "done":
        update_feature_status(conn, feature_id, "done")

    # TODO: Cleanup git worktrees
    # TODO: Close tmux sessions
    # TODO: Archive logs
    logger.warning("Feature cleanup not fully implemented")


# =============================================================================
# T052: File overlap validation between convoys
# =============================================================================

def check_file_overlap(
    conn: sqlite3.Connection,
    feature_id: str,
    proposed_files: list[str],
) -> list[dict[str, Any]]:
    """
    Check if proposed files overlap with existing convoys.

    Args:
        conn: Database connection
        feature_id: Feature identifier
        proposed_files: List of file paths to check

    Returns:
        List of conflicts, each with keys: convoy_id, overlapping_files
    """
    import json

    conflicts = []

    # Get all convoys for this feature
    convoys = list_convoys_by_feature(conn, feature_id)

    for convoy in convoys:
        # Skip completed convoys
        if convoy["status"] == "done":
            continue

        # Parse convoy files (JSON array)
        convoy_files = json.loads(convoy["files"])

        # Find overlap
        overlapping = set(proposed_files) & set(convoy_files)

        if overlapping:
            conflicts.append({
                "convoy_id": convoy["id"],
                "convoy_status": convoy["status"],
                "overlapping_files": list(overlapping),
            })

    return conflicts


def validate_no_file_conflicts(
    conn: sqlite3.Connection,
    feature_id: str,
    proposed_files: list[str],
) -> None:
    """
    Validate that proposed files don't conflict with existing convoys.

    Args:
        conn: Database connection
        feature_id: Feature identifier
        proposed_files: List of file paths to check

    Raises:
        ValueError: If file conflicts are detected
    """
    conflicts = check_file_overlap(conn, feature_id, proposed_files)

    if conflicts:
        error_msg = f"File conflicts detected for feature {feature_id}:\n"
        for conflict in conflicts:
            convoy_id = conflict["convoy_id"]
            files = ", ".join(conflict["overlapping_files"])
            error_msg += f"  - Convoy {convoy_id}: {files}\n"

        logger.error(error_msg)
        raise ValueError(error_msg)


# =============================================================================
# T053: Block feature start if file conflicts detected
# =============================================================================

def validate_convoy_files_no_overlap(
    conn: sqlite3.Connection,
    feature_id: str,
) -> bool:
    """
    Validate all convoys in a feature have non-overlapping files.

    Args:
        conn: Database connection
        feature_id: Feature identifier

    Returns:
        True if no overlaps, False otherwise
    """
    import json

    convoys = list_convoys_by_feature(conn, feature_id)

    # Build file map: file -> list of convoy IDs
    file_map: dict[str, list[str]] = {}

    for convoy in convoys:
        convoy_id = convoy["id"]
        files = json.loads(convoy["files"])

        for file_path in files:
            if file_path not in file_map:
                file_map[file_path] = []
            file_map[file_path].append(convoy_id)

    # Check for files in multiple convoys
    conflicts = {
        file_path: convoy_ids
        for file_path, convoy_ids in file_map.items()
        if len(convoy_ids) > 1
    }

    if conflicts:
        logger.error(f"File overlaps detected in feature {feature_id}:")
        for file_path, convoy_ids in conflicts.items():
            logger.error(f"  {file_path}: {', '.join(convoy_ids)}")
        return False

    return True


# =============================================================================
# T054: Convoy file tracking
# =============================================================================

def get_convoy_files(
    conn: sqlite3.Connection,
    convoy_id: str,
) -> list[str]:
    """
    Get list of files for a convoy.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier

    Returns:
        List of file paths
    """
    import json

    convoy = get_convoy(conn, convoy_id)
    if not convoy:
        return []

    return json.loads(convoy["files"])


def update_convoy_files(
    conn: sqlite3.Connection,
    convoy_id: str,
    files: list[str],
) -> None:
    """
    Update files list for a convoy.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier
        files: New list of file paths
    """
    import json

    conn.execute(
        "UPDATE convoys SET files = ? WHERE id = ?",
        (json.dumps(files), convoy_id),
    )
    conn.commit()

    logger.info(f"Updated files for convoy {convoy_id}: {len(files)} files")


def add_file_to_convoy(
    conn: sqlite3.Connection,
    convoy_id: str,
    file_path: str,
) -> None:
    """
    Add a file to convoy's file list.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier
        file_path: File path to add
    """
    files = get_convoy_files(conn, convoy_id)

    if file_path not in files:
        files.append(file_path)
        update_convoy_files(conn, convoy_id, files)
        logger.info(f"Added {file_path} to convoy {convoy_id}")


def remove_file_from_convoy(
    conn: sqlite3.Connection,
    convoy_id: str,
    file_path: str,
) -> None:
    """
    Remove a file from convoy's file list.

    Args:
        conn: Database connection
        convoy_id: Convoy identifier
        file_path: File path to remove
    """
    files = get_convoy_files(conn, convoy_id)

    if file_path in files:
        files.remove(file_path)
        update_convoy_files(conn, convoy_id, files)
        logger.info(f"Removed {file_path} from convoy {convoy_id}")
