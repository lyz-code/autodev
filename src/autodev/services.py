"""Gather all the orchestration functionality required by the program to work.

Classes and functions that connect the different domain model objects with the adapters
and handlers to achieve the program's purpose.
"""

from typing import TYPE_CHECKING

from repository_orm import Repository

from .model import GitRepository

if TYPE_CHECKING:
    from .adapters.abstract import GitServers


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
