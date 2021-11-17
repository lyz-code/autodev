"""Test the models."""

import datetime

import pytest

from autodev.model import GitRepositoryState, WorkflowState

from ..factories import GitRepositoryFactory, WorkflowFactory, WorkflowRunFactory


@pytest.mark.freeze_time()
class TestGitRepository:
    """Test the logic of the GitRepository model."""

    @pytest.mark.parametrize(
        ("old_state", "workflow_state", "new_state"),
        [
            (
                GitRepositoryState.HEALTHY,
                WorkflowState.FAILURE,
                GitRepositoryState.BROKEN,
            ),
            (GitRepositoryState.HEALTHY, WorkflowState.ILL, GitRepositoryState.ILL),
            (GitRepositoryState.ILL, WorkflowState.SUCCESS, GitRepositoryState.HEALTHY),
            (GitRepositoryState.ILL, WorkflowState.FAILURE, GitRepositoryState.BROKEN),
            (
                GitRepositoryState.BROKEN,
                WorkflowState.SUCCESS,
                GitRepositoryState.HEALTHY,
            ),
            (GitRepositoryState.BROKEN, WorkflowState.ILL, GitRepositoryState.ILL),
        ],
    )
    def test_update_state_changes_to_new_state(
        self,
        old_state: GitRepositoryState,
        new_state: GitRepositoryState,
        workflow_state: WorkflowState,
    ) -> None:
        """
        Given: A repository in an old state
        When: Updating the state with a Workflow that makes the repository state change
        Then: The updated_at is updated and the state is changed according to the next
            rules:
                * A healthy repo changes to ill if there is an ill workflow.
                * A healthy repo changes to broken if there is a broken workflow.
                * An ill repo changes to healthy if all the workflows are in success
                    state.
                * An ill repo changes to broken if one workflow is in failure state.
                * A broken repo changes to healthy if all the workflows are in success
                    state.
                * A broken repo changes to ill if one workflow is in ill state.
        """
        git_repo = GitRepositoryFactory(state=old_state)
        now = datetime.datetime.now()
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state="success"
        )
        workflows.append(WorkflowFactory(repo_id=git_repo.id_, state=workflow_state))

        git_repo.update_state(workflows)  # act

        assert git_repo.state == new_state
        assert git_repo.updated_at == now

    def test_update_state_stays_healthy(self) -> None:
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

    @pytest.mark.parametrize(
        ("workflow_state", "old_state"),
        [
            (WorkflowState.FAILURE, GitRepositoryState.BROKEN),
            (WorkflowState.ILL, GitRepositoryState.ILL),
        ],
    )
    def test_update_state_stays_not_healthy(
        self, old_state: GitRepositoryState, workflow_state: WorkflowState
    ) -> None:
        """
        Given: A broken or ill repository
        When: Updating the state with some Workflows in the same unhealthy state
        Then: The state is not changed and the updated_at is not updated.
        """
        git_repo = GitRepositoryFactory(state=old_state)
        workflows = WorkflowFactory.create_batch(
            3, repo_id=git_repo.id_, state=workflow_state
        )

        git_repo.update_state(workflows)  # act

        assert git_repo.state == old_state
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
    def test_update_on_push_events_with_state_change(
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
    def test_update_on_push_events_without_state_change(
        self, old_state: WorkflowState, new_state: WorkflowState
    ) -> None:
        """
        Given: A successful or failed workflow
        When: Updating the state with the latest WorkflowRun in the same state, which
            is a push to the monitored workflow branch.
        Then: Nor the state nor updated_at are updated
        """
        workflow = WorkflowFactory(state=old_state)
        last_update = workflow.updated_at
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state=old_state,
            event="push",
            branch=workflow.branch,
        )

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == old_state
        assert workflow.updated_at == last_update

    @pytest.mark.parametrize(
        ("old_state", "last_run_state", "new_state", "last_state_change"),
        [
            (WorkflowState.SUCCESS, WorkflowState.FAILURE, WorkflowState.ILL, 8),
            (WorkflowState.SUCCESS, WorkflowState.FAILURE, WorkflowState.ILL, 2),
            (WorkflowState.ILL, WorkflowState.FAILURE, WorkflowState.FAILURE, 8),
            (WorkflowState.ILL, WorkflowState.SUCCESS, WorkflowState.SUCCESS, 2),
            (WorkflowState.ILL, WorkflowState.SUCCESS, WorkflowState.SUCCESS, 8),
            (WorkflowState.FAILURE, WorkflowState.SUCCESS, WorkflowState.SUCCESS, 2),
            (WorkflowState.FAILURE, WorkflowState.SUCCESS, WorkflowState.SUCCESS, 8),
        ],
    )
    def test_update_on_schedule_events_with_state_change(
        self,
        old_state: WorkflowState,
        last_run_state: WorkflowState,
        new_state: WorkflowState,
        last_state_change: int,
    ) -> None:
        """
        Given: A workflow in an old_state
        When: Updating the state with WorkflowRuns in last_run_state
        Then: The workflow state is changed to new_state and the updated_at is updated
            because one of the next cases is met:

            * A Workflow in state success, when the last run is in failure state, the
                workflow's new state is ill. Disregarding the last time the state
                changed.
            * A Workflow in state ill, when the last run is in failure state, and the
                workflow state hasn't changed in more than the scheduled_tolerance
                number of days, the new state is failure.
            * A Workflow in failure or ill state, when the last run is in success
                state, the workflow's new state is success. Disregarding the last time
                the state changed.
        """
        now = datetime.datetime.now()
        last_update = now - datetime.timedelta(days=last_state_change)
        workflow = WorkflowFactory(
            state=old_state, scheduled_tolerance=7, updated_at=last_update
        )
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state=last_run_state,
            event="schedule",
            branch=workflow.branch,
        )

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == new_state
        assert workflow.updated_at == now

    @pytest.mark.parametrize(
        ("old_state", "last_run_state", "last_state_change"),
        [
            (WorkflowState.SUCCESS, WorkflowState.SUCCESS, 8),
            (WorkflowState.SUCCESS, WorkflowState.SUCCESS, 2),
            (WorkflowState.ILL, WorkflowState.FAILURE, 2),
            (WorkflowState.FAILURE, WorkflowState.FAILURE, 8),
            (WorkflowState.FAILURE, WorkflowState.FAILURE, 2),
        ],
    )
    def test_update_on_schedule_events_without_state_change(
        self,
        old_state: WorkflowState,
        last_run_state: WorkflowState,
        last_state_change: int,
    ) -> None:
        """
        Given: A workflow in an old_state
        When: Updating the state with WorkflowRuns in last_run_state
        Then: The workflow state and the updated_at are not changed because one of
            the next cases is met:

            * A Workflow in state success, when the last run is in success state.
                Disregarding the last time the state changed.
            * A Workflow in state ill, when the last run is in failure state, but
                the workflow has been in ill state for less than the scheduled_tolerance
                number of days.
            * A Workflow in state failure, when the last run is in failure state.
                Disregarding the last time the state changed.
        """
        now = datetime.datetime.now()
        last_update = now - datetime.timedelta(days=last_state_change)
        workflow = WorkflowFactory(
            state=old_state, scheduled_tolerance=7, updated_at=last_update
        )
        workflow_runs = WorkflowRunFactory.create_batch(
            3,
            workflow_id=workflow.id_,
            state=last_run_state,
            event="schedule",
            branch=workflow.branch,
        )

        workflow.update_state(workflow_runs)  # act

        assert workflow.state == old_state
        assert workflow.updated_at == last_update
