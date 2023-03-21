"""Define the factories of the program models."""

from pydantic_factories import ModelFactory

from autodev.model import GitRepository, Provider, Workflow, WorkflowRun


class GitRepositoryFactory(ModelFactory):  # type: ignore
    """Generate a fake factory."""

    __model__ = GitRepository


class WorkflowFactory(ModelFactory):  # type: ignore
    """Generate a fake factory."""

    __model__ = Workflow


class WorkflowRunFactory(ModelFactory):  # type: ignore
    """Generate a fake factory."""

    __model__ = WorkflowRun


class ProviderFactory(ModelFactory):  # type: ignore
    """Generate a fake provider."""

    __model__ = Provider
