"""Define the adapter for Github."""

from typing import List, Optional, Union

from github import Github as GithubAPI
from github.Repository import Repository as GithubRepository

from ..model import (
    GitRepository,
    GitRepositoryState,
    Workflow,
    WorkflowRun,
    WorkflowState,
)
from .abstract import GitServer


class Github(GitServer):
    """Define the Github adapter."""

    def __init__(self, name: str, token: str) -> None:
        """Initialize the adapter."""
        self.gh = GithubAPI(token)
        self.gh_repo: Optional[GithubRepository] = None
        self.name = name

    def get_repo(self, repo_id: Union[str, int]) -> "GitRepository":
        """Build GitRepository object from the data in the git server.

        Args:
            repo_id: identifier of the repository in the git server.
        """
        gh_repo = self.gh.get_repo(repo_id)
        self.gh_repo = gh_repo
        return GitRepository(
            source_id=gh_repo.id,
            name=gh_repo.name,
            description=gh_repo.description,
            open_issues=gh_repo.open_issues,
            stars=gh_repo.stargazers_count,
            forks=gh_repo.forks,
            created_at=gh_repo.created_at,
            language=gh_repo.language,
            clone_url=gh_repo.clone_url,
            default_branch=gh_repo.default_branch,
            state=GitRepositoryState.UNKNOWN,
            provider=self.name,
        )

    def get_repo_workflows(self, repo: GitRepository) -> "List[Workflow]":
        """Build the repository Workflow objects from the data in the git server."""
        if self.gh_repo is None or self.gh_repo.id != repo.source_id:
            self.gh_repo = self.gh.get_repo(repo.source_id)
        gh_workflows = self.gh_repo.get_workflows().get_page(0)
        return [
            Workflow(
                repo_id=repo.id_,
                source_id=gh_workflow.id,
                name=gh_workflow.name,
                state=WorkflowState.UNKNOWN,
                provider=self.name,
                scheduled_tolerance=repo.scheduled_tolerance,
            )
            for gh_workflow in gh_workflows
        ]

    def get_workflow_runs(self, workflow: Workflow) -> "List[WorkflowRun]":
        """Build the Workflow WorkflowRun objects from the data in the git server."""
        if self.gh_repo is None or self.gh_repo.id != workflow.repo_id:
            self.gh_repo = self.gh.get_repo(workflow.repo_id)
        gh_workflow = self.gh_repo.get_workflow(workflow.source_id)
        gh_workflow_runs = gh_workflow.get_runs().get_page(0)
        workflows = []
        for gh_run in gh_workflow_runs:
            if gh_run.status == "queued":
                state = WorkflowState.IN_PROGRESS
            elif gh_run.status == "completed" and gh_run.conclusion == "success":
                state = WorkflowState.SUCCESS
            elif gh_run.status == "completed" and gh_run.conclusion == "failure":
                state = WorkflowState.FAILURE
            else:
                state = WorkflowState.UNKNOWN
            workflows.append(
                WorkflowRun(
                    workflow_id=workflow.id_,
                    source_id=gh_run.id,
                    state=state,
                    branch=gh_run.head_branch,
                    created_at=gh_run.created_at,
                    updated_at=gh_run.updated_at,
                    event=gh_run.event,
                    url=gh_run.html_url,
                    provider=self.name,
                )
            )
        return workflows
