"""Tests the service layer."""

import pytest
from repository_orm import Repository, load_repository

from autodev import services
from autodev.model import (
    GitRepository,
    GitRepositoryState,
    Workflow,
    WorkflowRun,
    WorkflowState,
)

from .. import factories
from ..adapters import FakeGitServer


@pytest.fixture(name="repo")
def repo_() -> Repository:
    """Create a fake repository."""
    return load_repository([GitRepository, Workflow, WorkflowRun])


@pytest.fixture(name="adapter")
def adapter_(repo: Repository) -> FakeGitServer:
    """Create a fake git server."""
    adapter = FakeGitServer()
    repo.add(adapter._repo)
    repo.commit()
    return adapter


class TestGitRepoUpdate:
    """Test the update of git repositories."""

    def test_update_sets_workflow_and_repo_as_broken_if_main_branch_is_broken(
        self, repo: Repository, adapter: FakeGitServer
    ) -> None:
        """
        Given: A git repository with two workflows, one has all runs in green while the
            other has the last run broken affecting the main branch
        When: update is called
        Then: The repository and failing workflow are marked as broken.
        """
        successful_workflow_runs = factories.WorkflowRunFactory.create_batch(
            3,
            workflow_id=0,
            state=WorkflowState.SUCCESS,
            branch=adapter._workflows[0].branch,
            event="push",
        )
        failed_workflow_runs = factories.WorkflowRunFactory.create_batch(
            3,
            workflow_id=1,
            state=WorkflowState.SUCCESS,
            branch=adapter._workflows[1].branch,
            event="push",
        )
        max(failed_workflow_runs).state = WorkflowState.FAILURE
        adapter._workflow_runs = successful_workflow_runs + failed_workflow_runs

        services.update_git_repositories(repo, {0: adapter})  # act

        workflows = repo.all(Workflow)
        assert workflows[0].state == WorkflowState.SUCCESS
        assert workflows[1].state == WorkflowState.FAILURE
        assert workflows[2].state == WorkflowState.UNKNOWN
        assert repo.all(GitRepository)[0].state == GitRepositoryState.BROKEN
