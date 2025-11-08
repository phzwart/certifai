"""Git helper utilities used by certifai."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import InvalidGitRepositoryError


@lru_cache(maxsize=1)
def get_repo(start_path: Path | None = None) -> Optional[Repo]:
    """Return a GitPython Repo rooted at or above the provided path."""

    search_path = start_path or Path.cwd()
    try:
        return Repo(search_path, search_parent_directories=True)
    except InvalidGitRepositoryError:
        return None


def describe_line(path: Path, lineno: int) -> dict[str, str] | None:
    """Return commit metadata for a specific line within a file."""

    repo = get_repo(path)
    if repo is None:
        return None
    try:
        relpath = path.resolve().relative_to(Path(repo.working_tree_dir).resolve())
    except ValueError:
        return None
    blame_entries = repo.blame("HEAD", str(relpath))
    current_line = 0
    for commit, lines in blame_entries:
        for _ in lines:
            current_line += 1
            if current_line == lineno:
                committed_datetime = commit.committed_datetime.isoformat()
                return {
                    "commit": commit.hexsha,
                    "author": commit.author.name,
                    "email": commit.author.email,
                    "timestamp": committed_datetime,
                }
    return None
