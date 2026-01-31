"""Worktree management for agent isolation."""

import shutil
from pathlib import Path
from typing import Optional

import git

from ai_sprint.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# T049: Worktree creation (one per developer)
# =============================================================================

class WorktreeManager:
    """
    Manage Git worktrees for agent isolation.

    Each developer agent gets its own worktree to prevent merge conflicts.
    """

    def __init__(self, repo_path: str = "."):
        """
        Initialize worktree manager.

        Args:
            repo_path: Path to main git repository
        """
        self.repo = git.Repo(repo_path)
        if self.repo.bare:
            raise ValueError("Cannot create worktrees in bare repository")

        self.worktree_base = Path(repo_path) / "worktrees"
        self.worktree_base.mkdir(exist_ok=True)

    def create_worktree(
        self,
        agent_id: str,
        convoy_id: str,
        base_branch: str = "main",
    ) -> Path:
        """
        Create a new worktree for an agent.

        Args:
            agent_id: Unique agent identifier (e.g., "dev-001")
            convoy_id: Convoy being worked on
            base_branch: Branch to base work on (default: main)

        Returns:
            Path to created worktree

        Raises:
            ValueError: If worktree already exists
        """
        worktree_path = self.worktree_base / agent_id
        branch_name = f"{convoy_id}-{agent_id}"

        if worktree_path.exists():
            raise ValueError(f"Worktree already exists: {worktree_path}")

        logger.info(f"Creating worktree for {agent_id}: {worktree_path}")

        try:
            # Create new branch from base
            self.repo.git.worktree(
                "add",
                "-b",
                branch_name,
                str(worktree_path),
                base_branch,
            )

            logger.info(f"Worktree created: {worktree_path} (branch: {branch_name})")
            return worktree_path

        except git.GitCommandError as e:
            logger.error(f"Failed to create worktree: {e}")
            raise


# =============================================================================
# T050: Worktree cleanup on convoy completion
# =============================================================================

    def remove_worktree(
        self,
        agent_id: str,
        force: bool = False,
    ) -> None:
        """
        Remove a worktree when convoy is complete.

        Args:
            agent_id: Agent identifier
            force: Force removal even if worktree has uncommitted changes

        Raises:
            ValueError: If worktree doesn't exist
        """
        worktree_path = self.worktree_base / agent_id

        if not worktree_path.exists():
            raise ValueError(f"Worktree not found: {worktree_path}")

        logger.info(f"Removing worktree: {worktree_path}")

        try:
            # Remove worktree via git
            args = ["remove", str(worktree_path)]
            if force:
                args.append("--force")

            self.repo.git.worktree(*args)

            # Clean up any remaining directory
            if worktree_path.exists():
                shutil.rmtree(worktree_path)

            logger.info(f"Worktree removed: {worktree_path}")

        except git.GitCommandError as e:
            logger.error(f"Failed to remove worktree: {e}")
            raise

    def cleanup_all_worktrees(self) -> int:
        """
        Clean up all worktrees (use after feature completion).

        Returns:
            Number of worktrees removed
        """
        count = 0
        for worktree_path in self.worktree_base.iterdir():
            if worktree_path.is_dir():
                try:
                    agent_id = worktree_path.name
                    self.remove_worktree(agent_id, force=True)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup {worktree_path}: {e}")

        return count


# =============================================================================
# T051: Branch management (unique branch per worktree)
# =============================================================================

    def get_worktree_branch(self, agent_id: str) -> Optional[str]:
        """
        Get the branch name for a worktree.

        Args:
            agent_id: Agent identifier

        Returns:
            Branch name or None if worktree doesn't exist
        """
        worktree_path = self.worktree_base / agent_id

        if not worktree_path.exists():
            return None

        try:
            # Parse git worktree list to find branch
            worktree_list = self.repo.git.worktree("list", "--porcelain")

            for block in worktree_list.split("\n\n"):
                lines = block.split("\n")
                wt_path = None
                branch = None

                for line in lines:
                    if line.startswith("worktree "):
                        wt_path = line.split(" ", 1)[1]
                    elif line.startswith("branch "):
                        branch = line.split(" ", 1)[1].replace("refs/heads/", "")

                if wt_path and Path(wt_path) == worktree_path:
                    return branch

            return None

        except git.GitCommandError:
            return None

    def list_worktrees(self) -> list[dict[str, str]]:
        """
        List all active worktrees.

        Returns:
            List of worktree info dicts with keys: agent_id, path, branch
        """
        worktrees = []

        for worktree_path in self.worktree_base.iterdir():
            if worktree_path.is_dir():
                agent_id = worktree_path.name
                branch = self.get_worktree_branch(agent_id)

                worktrees.append({
                    "agent_id": agent_id,
                    "path": str(worktree_path),
                    "branch": branch or "unknown",
                })

        return worktrees

    def merge_worktree_branch(
        self,
        agent_id: str,
        target_branch: str = "main",
    ) -> None:
        """
        Merge worktree branch into target branch.

        Args:
            agent_id: Agent identifier
            target_branch: Branch to merge into (default: main)

        Raises:
            ValueError: If worktree or branch doesn't exist
        """
        branch = self.get_worktree_branch(agent_id)
        if not branch:
            raise ValueError(f"No branch found for worktree: {agent_id}")

        logger.info(f"Merging {branch} into {target_branch}")

        try:
            # Checkout target branch
            self.repo.git.checkout(target_branch)

            # Merge with fast-forward only
            self.repo.git.merge(branch, "--ff-only")

            logger.info(f"Successfully merged {branch} into {target_branch}")

        except git.GitCommandError as e:
            logger.error(f"Merge failed: {e}")
            raise

    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Delete a branch after merge.

        Args:
            branch_name: Branch to delete
            force: Force deletion even if not fully merged
        """
        logger.info(f"Deleting branch: {branch_name}")

        try:
            args = ["branch", "-d" if not force else "-D", branch_name]
            self.repo.git.execute(args)

            logger.info(f"Branch deleted: {branch_name}")

        except git.GitCommandError as e:
            logger.error(f"Failed to delete branch: {e}")
            raise
