"""Git helpers for worktree operations."""

from pathlib import Path
from typing import Optional

import git


class WorktreeManager:
    """Manage git worktrees for agent isolation."""

    def __init__(self, repo_path: str = ".") -> None:
        """
        Initialize worktree manager.

        Args:
            repo_path: Path to main git repository
        """
        self.repo = git.Repo(repo_path)

    def create_worktree(self, agent_id: str, branch_name: Optional[str] = None) -> str:
        """
        Create isolated worktree for agent.

        Args:
            agent_id: Agent identifier (e.g., "dev-001")
            branch_name: Optional branch name (defaults to agent_id)

        Returns:
            Path to created worktree

        Raises:
            git.GitCommandError: If worktree creation fails
        """
        branch = branch_name or agent_id
        worktree_path = Path("worktrees") / agent_id

        # Create worktrees directory if it doesn't exist
        worktree_path.parent.mkdir(parents=True, exist_ok=True)

        # Create worktree with new branch
        self.repo.git.worktree("add", str(worktree_path), "-b", branch)

        return str(worktree_path)

    def remove_worktree(self, agent_id: str, force: bool = False) -> None:
        """
        Remove agent worktree.

        Args:
            agent_id: Agent identifier
            force: Force removal even if dirty

        Raises:
            git.GitCommandError: If worktree removal fails
        """
        worktree_path = Path("worktrees") / agent_id

        if force:
            self.repo.git.worktree("remove", str(worktree_path), "--force")
        else:
            self.repo.git.worktree("remove", str(worktree_path))

    def list_worktrees(self) -> list[dict[str, str]]:
        """
        List all worktrees.

        Returns:
            List of worktree info dicts with 'path' and 'branch' keys
        """
        output = self.repo.git.worktree("list", "--porcelain")
        worktrees = []
        current_worktree: dict[str, str] = {}

        for line in output.split("\n"):
            if line.startswith("worktree "):
                if current_worktree:
                    worktrees.append(current_worktree)
                current_worktree = {"path": line.split(" ", 1)[1]}
            elif line.startswith("branch "):
                current_worktree["branch"] = line.split(" ", 1)[1]

        if current_worktree:
            worktrees.append(current_worktree)

        return worktrees

    def cleanup_worktrees(self) -> None:
        """Remove all agent worktrees in worktrees/ directory."""
        worktrees_dir = Path("worktrees")
        if not worktrees_dir.exists():
            return

        for agent_dir in worktrees_dir.iterdir():
            if agent_dir.is_dir():
                try:
                    self.remove_worktree(agent_dir.name, force=True)
                except git.GitCommandError:
                    # Already removed or doesn't exist
                    pass


def validate_git_repo(repo_path: str = ".") -> bool:
    """
    Validate that path is a git repository.

    Args:
        repo_path: Path to check

    Returns:
        True if valid git repo, False otherwise
    """
    try:
        git.Repo(repo_path)
        return True
    except (git.InvalidGitRepositoryError, git.NoSuchPathError):
        return False
