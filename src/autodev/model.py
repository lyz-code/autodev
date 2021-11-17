"""Define the models of the program."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from repository_orm import Entity


class GitServerType(str, Enum):
    """Define the possible Git Server types."""

    GITHUB = "github"


class Provider(Entity):
    """Define the Git/CI server providers."""

    name: str
    token_path: Optional[str]
    git_server: GitServerType
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()


class GitRepositoryState(str, Enum):
    """Define the possible Git Repository states."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    BROKEN = "broken"
    DELETED = "deleted"
    ILL = "ill"


class GitRepository(Entity):
    """Define the information of a git repository."""

    name: str
    description: str
    stars: int
    forks: int
    source_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    state: GitRepositoryState = GitRepositoryState.UNKNOWN
    language: Optional[str]
    clone_url: str
    monitor_workflows: bool = False
    default_branch: str = "master"
    open_issues: Optional[int] = None
    provider_id: Optional[int] = None
    path: Optional[str] = None
    scheduled_tolerance: int = 7

    def set_state(self, state: GitRepositoryState) -> None:
        """Set the new state to the workflow.

        If it changes, it will update the updated_at date.
        """
        if state != self.state:
            self.updated_at = datetime.now()
            self.state = state

    def update_state(self, workflows: List["Workflow"]) -> None:
        """Update the Git Repository state with the workflow states.

        If one of the workflows is marked as failure, the state is set as broken.
        """
        state = GitRepositoryState.HEALTHY
        for workflow in workflows:
            if workflow.state == WorkflowState.FAILURE:
                state = GitRepositoryState.BROKEN
                break
            elif workflow.state == WorkflowState.ILL:
                state = GitRepositoryState.ILL
        self.set_state(state)


class WorkflowEvent(str, Enum):
    """Define the possible Workflow events."""

    PUSH = "push"
    SCHEDULE = "schedule"


class WorkflowState(str, Enum):
    """Define the possible Workflow state."""

    UNKNOWN = "unknown"
    IN_PROGRESS = "in progress"
    SUCCESS = "success"
    FAILURE = "failure"
    ILL = "ill"


class Workflow(Entity):
    """Define the information of a CI workflow."""

    source_id: int
    repo_id: int
    name: str
    state: WorkflowState = WorkflowState.UNKNOWN
    updated_at: datetime = datetime.now()
    branch: str = "master"
    scheduled_tolerance: int = 7

    def set_state(self, state: WorkflowState) -> None:
        """Set the new state to the workflow.

        If it changes, it will update the updated_at date.
        """
        if state != self.state:
            self.updated_at = datetime.now()
            self.state = state

    def update_state(self, workflow_runs: List["WorkflowRun"]) -> None:
        """Update the Workflow state with the workflow runs states.

        The workflow will be marked as failure if:

        * In push workflows, if the latest run is in failure state.
        * In schedule workflows, if the latest run is in failure state and the workflow
            has been in that state for the scheduled_tolerance number of days.

        The workflow will be marked as success if the last run is successful.

        The workflow will be marked as ill if a scheduled workflow is in failure state
        and it has been in that state a smaller number of days than scheduled_tolerance.
        """
        for run in sorted(workflow_runs, reverse=True):
            if run.branch != self.branch:
                continue
            if run.event == WorkflowEvent.PUSH or run.state == WorkflowState.SUCCESS:
                self.set_state(run.state)
                return
            if self.state == WorkflowState.SUCCESS:
                self.set_state(WorkflowState.ILL)
                return

            last_state_change = (datetime.now() - self.updated_at).days
            if last_state_change > self.scheduled_tolerance:
                self.set_state(WorkflowState.FAILURE)
                return


class WorkflowRun(Entity):
    """Define the information of a CI workflow run."""

    workflow_id: int
    source_id: int
    state: WorkflowState
    branch: str
    created_at: datetime
    updated_at: datetime
    event: WorkflowEvent
    url: Optional[str] = None
    provider: Optional[str] = None

    # ignore: Argument 1 of "__gt__" is incompatible with supertype "Entity";
    # supertype defines the argument type as "Entity". We are not breaking any
    # compatibility with Entity.
    def __gt__(self, other: "WorkflowRun") -> bool:  # type: ignore
        """Compare if it's greater than the other object."""
        return self.created_at > other.created_at

    def __lt__(self, other: "WorkflowRun") -> bool:  # type: ignore
        """Compare if it's smaller than the other object."""
        return self.created_at < other.created_at
