"""Define the stub of the Github library."""

from datetime import datetime
from typing import Any, List

from pydantic import BaseModel


class WorkflowRunStub(BaseModel):
    """Stub the Github WorkflowRun object."""

    # VNE003: variable names that shadow builtins are not allowed, it's how the API is
    id: int = 1234525  # noqa: VNE003
    head_branch: str = "master"
    event: str = "schedule"
    status: str = "completed"
    run_number: int = 35
    conclusion: str = "success"
    workflow_id: int = 9769400
    html_url: str = "https://github.com/test/test/actions/runs/1234525"
    name: str = "Test"
    created_at: datetime = datetime(2019, 11, 19, 12, 13, 16)
    updated_at: datetime = datetime(2019, 11, 19, 12, 13, 16)


class WorkflowStub(BaseModel):
    """Stub the Github Workflow object."""

    # VNE003: variable names that shadow builtins are not allowed, it's how the API is
    id: int = 9769400  # noqa: VNE003
    name: str = "Test"
    created_at: datetime = datetime(2019, 11, 19, 12, 13, 16)
    updated_at: datetime = datetime(2019, 11, 19, 12, 13, 16)
    workflow_runs_: List[WorkflowRunStub] = [WorkflowRunStub()]

    def get_runs(self) -> "PaginatedListStub":
        """Return the workflow runs."""
        return PaginatedListStub(objects_=self.workflow_runs_)


class GitRepositoryStub(BaseModel):
    """Stub the Github Repository object."""

    # VNE003: variable names that shadow builtins are not allowed, it's how the API is
    id: int = 12345125  # noqa: VNE003
    name: str = "Repository name"
    description: str = "Repository description"
    open_issues: int = 10
    stargazers_count: int = 10
    forks: int = 2
    created_at: datetime = datetime(2019, 11, 19, 12, 13, 16)
    language: str = "Python"
    clone_url: str = "https://github.com/test/test"
    default_branch: str = "master"
    workflows_: List[WorkflowStub] = [WorkflowStub()]

    def get_workflows(self) -> "PaginatedListStub":
        """Return a repository."""
        return PaginatedListStub(objects_=self.workflows_)

    def get_workflow(self, workflow_id: int) -> "WorkflowStub":
        """Return a repository."""
        return self.workflows_[0]


class GithubStub(BaseModel):
    """Stub the Github object."""

    repo_: GitRepositoryStub = GitRepositoryStub()

    def get_repo(self, repo_id: str) -> GitRepositoryStub:
        """Return a repository."""
        return self.repo_


class PaginatedListStub(BaseModel):
    """Stub a Github paginated object."""

    objects_: List[Any]

    def get_page(self, page_id: int) -> List[Any]:
        """Return the objects of that page."""
        return self.objects_
