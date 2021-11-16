"""Test the models."""

import datetime

import pytest

from autodev.model import GitRepositoryState, WorkflowState

from ..factories import GitRepositoryFactory, WorkflowFactory, WorkflowRunFactory


@pytest.mark.freeze_time()
class TestGitRepository:
    """Test the logic of the GitRepository model."""

    def test_update_state_changes_from_healthy_to_broken(self) -> None:
        """
        Given: A healthy repository
        When: Updating the state with a Workflow in state Failure
        Then: The state is changed and the updated_at is updated.
        """
        git_repo = GitRepositoryFactory(state="healthy")
        now = datetime.datetime.now()
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state="success"
        )
        workflows.append(WorkflowFactory(repo_id=git_repo.id_, state="failure"))

        git_repo.update_state(workflows)  # act

        assert git_repo.state == GitRepositoryState.BROKEN
        assert git_repo.updated_at == now

    def test_update_state_changes_from_broken_to_healthy(self) -> None:
        """
        Given: A broken repository
        When: Updating the state with all Workflows in success state
        Then: The state is changed and the updated_at is updated.
        """
        git_repo = GitRepositoryFactory(state="broken")
        now = datetime.datetime.now()
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state="success"
        )

        git_repo.update_state(workflows)  # act

        assert git_repo.state == GitRepositoryState.HEALTHY
        assert git_repo.updated_at == now

    def test_update_state_changes_from_healthy_to_healthy(self) -> None:
        """
        Given: A healthy repository
        When: Updating the state with all Workflows in success state
        Then: The state is not changed and the updated_at is not updated.
        """
        git_repo = GitRepositoryFactory(state="healthy")
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state="success"
        )

        git_repo.update_state(workflows)  # act

        assert git_repo.state == GitRepositoryState.HEALTHY
        assert git_repo.updated_at is None

    def test_update_state_changes_from_broken_to_broken(self) -> None:
        """
        Given: A healthy repository
        When: Updating the state with all Workflows in success state
        Then: The state is not changed and the updated_at is not updated.
        """
        git_repo = GitRepositoryFactory(state="broken")
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state="failure"
        )

        git_repo.update_state(workflows)  # act

        assert git_repo.state == GitRepositoryState.BROKEN
        assert git_repo.updated_at is None


@pytest.mark.freeze_time()
class TestWorkflow:
    """Test the logic of the Workflow model."""

    @pytest.mark.parametrize(
        ("old_state", "new_state"),
        [
            (WorkflowState.SUCCESS, WorkflowState.FAILURE),
            (WorkflowState.FAILURE, WorkflowState.SUCCESS),
        ],
    )
    def test_update_state_changes_from_state_on_push_events(
        self, old_state: WorkflowState, new_state: WorkflowState
    ) -> None:
        """
        Given: A successful or failed workflow
        When: Updating the state with the latest WorkflowRun in the other state, which
            is a push to the monitored workflow branch.
        Then: The state is changed and the updated_at is updated.
        """
        workflow = WorkflowFactory(state=old_state)
        now = datetime.datetime.now()
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state=old_state,
            event="push",
            branch=workflow.branch,
        )
        max(workflow_runs).state = new_state

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == new_state
        assert workflow.updated_at == now

    @pytest.mark.parametrize(
        ("old_state", "new_state"),
        [
            (WorkflowState.SUCCESS, WorkflowState.SUCCESS),
            (WorkflowState.FAILURE, WorkflowState.FAILURE),
        ],
    )
    def test_update_state_changes_from_same_state_on_push_events(
        self, old_state: WorkflowState, new_state: WorkflowState
    ) -> None:
        """
        Given: A successful or failed workflow
        When: Updating the state with the latest WorkflowRun in the same state, which
            is a push to the monitored workflow branch.
        Then: Nor the state nor updated_at are updated
        """
        workflow = WorkflowFactory(state=old_state)
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state=old_state,
            event="push",
            branch=workflow.branch,
        )

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == old_state
        assert workflow.updated_at is None

    def test_update_state_changes_from_success_to_failure_on_schedule_events(
        self,
    ) -> None:
        """
        Given: A successful workflow
        When: Updating the state with WorkflowRuns in state failure, which
            is a scheduled to the monitored workflow branch, and the workflow has been
            in failure state for more than the scheduled_tolerance number of days.
        Then: The state and the updated_at are updated
        """
        now = datetime.datetime.now()
        last_update = now - datetime.timedelta(days=8)
        workflow = WorkflowFactory(
            state="success", scheduled_tolerance=7, updated_at=last_update
        )
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state="failure",
            event="schedule",
            branch=workflow.branch,
        )

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == WorkflowState.FAILURE
        assert workflow.updated_at == now
