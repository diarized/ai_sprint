"""Refinery agent - merge operations."""

import sqlite3
from pathlib import Path
from typing import Any, Optional

import git

from ai_sprint.config.settings import Settings
from ai_sprint.services.quality_gates import QualityGateRunner
from ai_sprint.services.state_manager import (
    get_db,
    get_task,
    list_tasks_by_convoy,
    publish_event,
    update_task_status,
)
from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T036: Refinery agent base (merge operations)
# =============================================================================

class RefineryAgent:
    """
    Refinery agent - handles code merging.

    Responsibilities:
    - Sequential merge queue management
    - Fast-forward merge strategy
    - Rebase before merge
    - Security scanning before merge
    - Trigger documentation updates
    """

    def __init__(
        self,
        db_path: str = "~/.ai-sprint/beads.db",
        settings: Optional[Settings] = None,
    ):
        """
        Initialize Refinery agent.

        Args:
            db_path: Path to SQLite database
            settings: Application settings
        """
        self.db_path = db_path
        self.settings = settings or Settings()

    def merge_task(self, task_id: str, worktree_path: Path) -> bool:
        """
        Merge a task's code changes.

        Implementation of T080: Integrate security gates into Refinery agent.

        Args:
            task_id: Task to merge
            worktree_path: Path to git worktree

        Returns:
            True if merge succeeded, False otherwise
        """
        logger.info(f"Merging task: {task_id}")

        with get_db(self.db_path) as conn:
            task = get_task(conn, task_id)
            if not task:
                logger.error(f"Task not found: {task_id}")
                return False

            if task["status"] != "in_docs":
                logger.error(f"Task {task_id} not ready for merge")
                return False

            # Run security gates before merge
            runner = QualityGateRunner(self.settings, worktree_path)
            results = runner.run_all_gates(stage="merge")

            if not runner.all_gates_passed():
                # Failed security gates - reject with specific feedback
                failure_message = runner.get_failure_message()
                logger.warning(f"Task {task_id} failed security gates: {failure_message}")

                self.reject_merge(task_id, failure_message)
                return False

            logger.info(f"Task {task_id} passed all security gates")

            # Mark task as done
            update_task_status(conn, task_id, "done")

            # Publish merge success event
            publish_event(
                conn,
                agent_id="manager",
                event_type="MERGE_TASK",
                payload={"task_id": task_id, "success": True},
            )

            return True

    def reject_merge(
        self,
        task_id: str,
        reason: str,
    ) -> None:
        """
        Reject merge and send task back to developer.

        Args:
            task_id: Task to reject
            reason: Rejection reason (security issues, conflicts, etc.)
        """
        logger.info(f"Rejecting merge for {task_id}: {reason}")

        with get_db(self.db_path) as conn:
            # Send back to in_progress
            update_task_status(conn, task_id, "in_progress")

            # Publish rework event
            publish_event(
                conn,
                agent_id="developer",
                event_type="REWORK_NEEDED",
                payload={"task_id": task_id, "reason": reason},
            )

    def trigger_documentation(self, convoy_id: str) -> None:
        """
        Trigger documentation update after convoy merge.

        Args:
            convoy_id: Convoy that was merged
        """
        logger.info(f"Triggering documentation for convoy: {convoy_id}")

        with get_db(self.db_path) as conn:
            publish_event(
                conn,
                agent_id="librarian",
                event_type="UPDATE_DOCS",
                payload={"convoy_id": convoy_id},
            )

    # =========================================================================
    # T058: Sequential merge queue
    # =========================================================================

    def get_merge_queue(self, convoy_id: str) -> list[str]:
        """
        Get tasks in merge queue (in_docs status) for a convoy.

        Args:
            convoy_id: Convoy identifier

        Returns:
            List of task IDs ready for merge, ordered by completion time
        """
        with get_db(self.db_path) as conn:
            tasks = list_tasks_by_convoy(conn, convoy_id, status="in_docs")

            # Sort by completed_at timestamp
            sorted_tasks = sorted(
                tasks,
                key=lambda t: t["completed_at"] or "",
            )

            return [t["id"] for t in sorted_tasks]

    def process_merge_queue(
        self,
        convoy_id: str,
        repo_path: Path,
        target_branch: str = "main",
    ) -> dict[str, Any]:
        """
        Process all tasks in merge queue sequentially.

        Args:
            convoy_id: Convoy identifier
            repo_path: Path to main git repository
            target_branch: Branch to merge into

        Returns:
            Summary dict with keys: merged, failed, total
        """
        queue = self.get_merge_queue(convoy_id)
        merged = []
        failed = []

        logger.info(f"Processing merge queue for {convoy_id}: {len(queue)} tasks")

        for task_id in queue:
            try:
                # Get task worktree path from task metadata
                # TODO: Store worktree path in task or agent_session
                worktree_path = repo_path / "worktrees" / f"task-{task_id}"

                if self.merge_task_ff(task_id, repo_path, target_branch):
                    merged.append(task_id)
                else:
                    failed.append(task_id)

            except Exception as e:
                logger.error(f"Failed to merge {task_id}: {e}")
                failed.append(task_id)

        return {
            "merged": merged,
            "failed": failed,
            "total": len(queue),
        }

    # =========================================================================
    # T059: Fast-forward merge strategy
    # =========================================================================

    def merge_task_ff(
        self,
        task_id: str,
        repo_path: Path,
        target_branch: str = "main",
    ) -> bool:
        """
        Merge task using fast-forward strategy.

        Args:
            task_id: Task to merge
            repo_path: Path to main repository
            target_branch: Branch to merge into

        Returns:
            True if merge succeeded, False otherwise
        """
        logger.info(f"Fast-forward merging task {task_id} into {target_branch}")

        try:
            repo = git.Repo(repo_path)

            with get_db(self.db_path) as conn:
                task = get_task(conn, task_id)
                if not task:
                    logger.error(f"Task not found: {task_id}")
                    return False

                # Get branch name for this task
                # TODO: Lookup branch from worktree or agent_session
                branch_name = f"task-{task_id}"

                # Checkout target branch
                repo.git.checkout(target_branch)

                # Attempt fast-forward merge
                try:
                    repo.git.merge(branch_name, "--ff-only")
                    logger.info(f"Fast-forward merge succeeded for {task_id}")

                    # Mark task as done
                    update_task_status(conn, task_id, "done")

                    return True

                except git.GitCommandError as e:
                    if "not possible to fast-forward" in str(e):
                        logger.warning(f"Fast-forward not possible for {task_id} - attempting rebase")
                        return self.rebase_and_merge(task_id, repo, branch_name, target_branch)
                    else:
                        raise

        except Exception as e:
            logger.error(f"Fast-forward merge failed for {task_id}: {e}")
            self.reject_merge(task_id, f"Merge failed: {e}")
            return False

    # =========================================================================
    # T060: Rebase before merge
    # =========================================================================

    def rebase_and_merge(
        self,
        task_id: str,
        repo: git.Repo,
        branch_name: str,
        target_branch: str,
    ) -> bool:
        """
        Rebase branch onto target, then fast-forward merge.

        Args:
            task_id: Task identifier
            repo: Git repository
            branch_name: Branch to rebase
            target_branch: Branch to rebase onto

        Returns:
            True if rebase and merge succeeded, False otherwise
        """
        logger.info(f"Rebasing {branch_name} onto {target_branch}")

        try:
            # Checkout task branch
            repo.git.checkout(branch_name)

            # Rebase onto target
            repo.git.rebase(target_branch)

            # Checkout target branch
            repo.git.checkout(target_branch)

            # Fast-forward merge (should succeed after rebase)
            repo.git.merge(branch_name, "--ff-only")

            logger.info(f"Rebase and merge succeeded for {task_id}")

            with get_db(self.db_path) as conn:
                update_task_status(conn, task_id, "done")

            return True

        except git.GitCommandError as e:
            if "conflict" in str(e).lower():
                logger.error(f"Rebase conflicts for {task_id}")
                self.reject_merge(task_id, f"Rebase conflicts: {e}")
            else:
                logger.error(f"Rebase failed for {task_id}: {e}")
                self.reject_merge(task_id, f"Rebase failed: {e}")

            # Abort rebase
            try:
                repo.git.rebase("--abort")
            except Exception:
                pass

            return False

    def cleanup_merged_branch(
        self,
        repo: git.Repo,
        branch_name: str,
    ) -> None:
        """
        Delete branch after successful merge.

        Args:
            repo: Git repository
            branch_name: Branch to delete
        """
        logger.info(f"Cleaning up merged branch: {branch_name}")

        try:
            repo.git.branch("-d", branch_name)
            logger.info(f"Branch deleted: {branch_name}")

        except git.GitCommandError as e:
            logger.warning(f"Failed to delete branch {branch_name}: {e}")
