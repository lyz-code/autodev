"""Define the adapters interfaces."""

import abc
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if TYPE_CHECKING:
    from ..model import GitRepository, Workflow, WorkflowRun

# The key is the Provider.id_, and the value is the configured GitServer instance.
GitServers = Dict[int, "GitServer"]


class GitServer(abc.ABC):
    """Define interface of the git servers."""

    name: str
    token: Optional[str] = None

    @abc.abstractmethod
    def get_repo(self, repo_id: Union[str, int]) -> "GitRepository":
        """Build GitRepository object from the data in the git server.

        Args:
            repo_id: identifier of the repository in the git server.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def get_repo_workflows(self, repo: "GitRepository") -> "List[Workflow]":
        """Build the repository Workflow objects from the data in the git server."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_workflow_runs(self, workflow: "Workflow") -> "List[WorkflowRun]":
        """Build the Workflow WorkflowRun objects from the data in the git server."""
        raise NotImplementedError
