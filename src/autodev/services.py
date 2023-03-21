"""Gather all the orchestration functionality required by the program to work.

Classes and functions that connect the different domain model objects with the adapters
and handlers to achieve the program's purpose.
"""

import io
import json
import logging
import os
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Tuple

from cruft._commands import check as cruft_template_updated
from cruft._commands import update as cruft_template_update
from git import Repo
from repository_orm import Repository

from .exceptions import CruftUpdateFailedError
from .model import GitRepository

if TYPE_CHECKING:
    from .adapters.abstract import GitServers

log = logging.getLogger(__name__)


def get_file_path(
    filename: str, starting_path: Optional[Path] = None
) -> Optional[Path]:
    """Search for a file by traversing up the tree from a path.

    Args:
        filename: the name of the file to search for
        starting_path: an optional path from which to start searching

    Returns:
        The `Path` to the file if it exists or `None` if it doesn't
    """
    start = starting_path or Path.cwd()

    for path in [start, *start.parents]:
        file_path = path / filename
        if file_path.is_file():
            return file_path

    return None


def get_cruft_template(cruft_file: Path) -> Tuple[str, str]:
    """Get the cruft template repository url and current commit."""
    with open(cruft_file, "r") as file_descriptor:
        cruft_data = json.loads(file_descriptor.read())

    return cruft_data["template"], cruft_data["commit"]


def start_cruft_update() -> Optional[str]:
    """Do the first steps to update the cruft template of a repository.

    It will:
        create the branch and update the
    cruft, once everything is ready to be committed, then it will create the commit
    message.

    Returns:
        template_url or None if the repository is updated
    """
    log.debug("Locating the .cruft.json file.")
    cruft_file = get_file_path(".cruft.json")
    if cruft_file is None:
        raise FileNotFoundError("Could not find the .cruft.json file of the repo.")

    repo = Repo(os.path.dirname(cruft_file))

    template_url, template_commit = get_cruft_template(cruft_file)
    new_branch_name = f"feat/update-cruft-{template_commit}"

    if repo.head.reference.name != new_branch_name:
        if cruft_template_updated():
            log.info("Already in the latest version of the template")
            return None

        log.debug("Updating the cookiecutter template.")
        output = io.StringIO()
        with redirect_stdout(output):
            update_succeeded = cruft_template_update()

        if not update_succeeded:
            cruft_output = output.getvalue()
            raise CruftUpdateFailedError(cruft_output)

        log.debug("Creating the new git branch.")
        new_branch = repo.create_head(new_branch_name)
        repo.head.reference = new_branch

    log.debug("Checking if the update needs human interaction")
    git = repo.git
    if "both modified" in git.status() or ".rej" in git.status():
        raise CruftUpdateFailedError(
            "The update didn't went smooth, you need to solve the conflicts "
            "yourself, but let me do the commit."
        )

    return template_url


def end_cruft_update(template_url: str) -> None:
    """Do the last steps to update the cruft template of a repository."""

    # To the next function
    log.debug("Cloning the template repository.")
    template_repo = Repo.clone_from(template_url, tempfile.mkdtemp())


def update_git_repositories(repo: Repository, adapters: "GitServers") -> None:
    """Update the information of the monitored git repositories."""
    update_git_repo_workflows(repo, adapters)


def update_git_repo_workflows(repo: Repository, adapters: "GitServers") -> None:
    """Update the workflows of the workflow monitored git repositories."""
    git_repos = repo.search({"monitor_workflows": True}, [GitRepository])
    for git_repo in git_repos:
        adapter = adapters[git_repo.provider_id]
        workflows = adapter.get_repo_workflows(git_repo)
        for workflow in workflows:
            workflow = repo.add(workflow)  # sets the id_
            workflow_runs = adapter.get_workflow_runs(workflow)
            for workflow_run in workflow_runs:
                repo.add(workflow_run)
            workflow.update_state(workflow_runs)
            repo.add(workflow)
        git_repo.update_state(workflows)
        repo.add(git_repo)
        repo.commit()
