"""Test the github adapter."""

from datetime import datetime

import pytest

from autodev.adapters.github import Github
from autodev.model import (
    GitRepository,
    GitRepositoryState,
    Workflow,
    WorkflowEvent,
    WorkflowRun,
    WorkflowState,
)

from ..factories import GitRepositoryFactory, WorkflowFactory
from ..stubs import GithubStub, GitRepositoryStub, WorkflowRunStub, WorkflowStub


@pytest.fixture(name="github")
def github_() -> Github:
    """Return the Github object with the GithubStub."""
    github = Github(name="test_github", token="token")
    # ignore: Incompatible types in assignment (expression has type "GithubStub",
    #   variable has type "Github"). It's what we want
    github.gh = GithubStub()  # type: ignore
    return github


def test_get_repo(github: Github) -> None:
    """
    Given: A configured Github adapter.
    When: using the get_repo method with a valid string.
    Then: The repository is returned.
    """
    desired_repo = GitRepository(
        name="Repository name",
        description="Repository description",
        open_issues=10,
        stars=10,
        forks=2,
        created_at=datetime(2019, 11, 19, 12, 13, 16),
        language="Python",
        clone_url="https://github.com/test/test",
        default_branch="master",
        state=GitRepositoryState.UNKNOWN,
        source_id=12345125,
    )

    result = github.get_repo("some/repo")

    assert result == desired_repo


def test_get_repo_workflows(github: Github) -> None:
    """
    Given: A configured Github adapter.
    When: using the get_repo_workflows method with a valid string.
    Then: The repository workflows are returned.
    """
    repo = GitRepositoryFactory.create()
    desired_workflows = [
        Workflow(
            repo_id=repo.id_,
            source_id=9769400,
            name="Test",
            state=WorkflowState.UNKNOWN,
            last_state_change=None,
            branch="master",
            scheduled_tolerance=repo.scheduled_tolerance,
        )
    ]

    result = github.get_repo_workflows(repo)

    assert result == desired_workflows


@pytest.mark.parametrize(
    ("gh_event", "event"),
    [("schedule", WorkflowEvent.SCHEDULE), ("push", WorkflowEvent.PUSH)],
)
@pytest.mark.parametrize(
    ("gh_status", "gh_conclusion", "state"),
    [
        ("queued", "", WorkflowState.IN_PROGRESS),
        ("completed", "success", WorkflowState.SUCCESS),
        ("completed", "failure", WorkflowState.FAILURE),
    ],
)
def test_get_repo_workflow_runs(
    github: Github,
    gh_status: str,
    gh_conclusion: str,
    state: WorkflowState,
    gh_event: str,
    event: WorkflowEvent,
) -> None:
    """
    Given: A configured Github adapter.
    When: using the get_workflow_runs method with a valid string for the different
        event and states.
    Then: The repository workflow runs are returned.
    """
    workflow = WorkflowFactory.create()
    github.gh_repo = GitRepositoryStub(id=workflow.repo_id)  # type: ignore
    github.gh_repo.workflows_ = [  # type: ignore
        WorkflowStub(
            workflow_runs_=[
                WorkflowRunStub(
                    status=gh_status, conclusion=gh_conclusion, event=gh_event
                )
            ]
        )
    ]
    desired_workflow_runs = [
        WorkflowRun(
            workflow_id=workflow.id_,
            source_id=1234525,
            name="Test",
            branch="master",
            event=event,
            state=state,
            url="https://github.com/test/test/actions/runs/1234525",
            created_at=datetime(2019, 11, 19, 12, 13, 16),
            updated_at=datetime(2019, 11, 19, 12, 13, 16),
            provider="test_github",
        )
    ]

    result = github.get_workflow_runs(workflow)

    assert result == desired_workflow_runs
