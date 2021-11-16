"""Define the fake adapters."""

from typing import TYPE_CHECKING, List, Union

from autodev.adapters.abstract import GitServer
from autodev.model import GitRepository, Workflow, WorkflowRun

from . import factories

if TYPE_CHECKING:
    from repository_orm import Entity


class FakeGitServer(GitServer):
    """Define a fake GitServer adapter for unit testing."""

    def __init__(self, name: str = "fake_git_server", token: str = "token") -> None:
        """Initialize the adapter."""
        self.name = name
        self.token = token
        self._repo = factories.GitRepositoryFactory.create(
            state="healthy",
            provider_id=0,
            monitor_workflows=True,
        )
        self._workflows = factories.WorkflowFactory.create_batch(
            3, repo_id=self._repo.id_, state="unknown"
        )
        self._workflow_runs = factories.WorkflowRunFactory.create_batch(
            3, workflow_id=self._workflows[0].id_
        )

    def get_repo(self, repo_id: Union[str, int]) -> "GitRepository":
        """Build GitRepository object from the data in the git server.

        Args:
            repo_id: identifier of the repository in the git server.
        """
        self._unset_ids([self._repo])
        return self._repo

    def get_repo_workflows(self, repo: "GitRepository") -> "List[Workflow]":
        """Build the Gitrepository Workflow objects from the data in the git server."""
        self._unset_ids(self._workflows)
        return self._workflows

    def get_workflow_runs(self, workflow: "Workflow") -> "List[WorkflowRun]":
        """Build the Workflow WorkflowRun objects from the data in the git server."""
        self._unset_ids(self._workflow_runs)
        return [run for run in self._workflow_runs if run.workflow_id == workflow.id_]

    def _unset_ids(self, entities: List["Entity"]) -> None:
        """Unset the entity id_.

        The adapters can't know it, but the factories set it.
        """
        for entity in entities:
            entity.id_ = -1
