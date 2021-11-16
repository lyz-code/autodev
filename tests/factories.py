"""Define the factories of the program models."""

import factory
from faker_enum import EnumProvider

from autodev.model import (
    GitRepository,
    GitRepositoryState,
    GitServerType,
    Provider,
    Workflow,
    WorkflowEvent,
    WorkflowRun,
    WorkflowState,
)

factory.Faker.add_provider(EnumProvider)


class GitRepositoryFactory(factory.Factory):  # type: ignore
    """Generate a fake factory."""

    id_ = factory.Faker("pyint")
    name = factory.Faker("word")
    description = factory.Faker("sentence")
    stars = factory.Faker("pyint")
    forks = factory.Faker("pyint")
    source_id = factory.Faker("pyint")
    created_at = factory.Faker("date_time")
    state = factory.Faker("enum", enum_cls=GitRepositoryState)
    language = factory.Faker("word")
    clone_url = factory.Faker("url")
    provider_id = factory.Faker("pyint")
    scheduled_tolerance = factory.Faker("pyint")

    class Meta:
        """Declare the model of the factory."""

        model = GitRepository


class WorkflowFactory(factory.Factory):  # type: ignore
    """Generate a fake factory."""

    id_ = factory.Faker("pyint")
    source_id = factory.Faker("pyint")
    repo_id = factory.Faker("pyint")
    name = factory.Faker("word")
    state = factory.Faker("enum", enum_cls=WorkflowState)
    branch = factory.Faker("word")

    class Meta:
        """Declare the model of the factory."""

        model = Workflow


class WorkflowRunFactory(factory.Factory):  # type: ignore
    """Generate a fake factory."""

    id_ = factory.Faker("pyint")
    workflow_id = factory.Faker("pyint")
    source_id = factory.Faker("pyint")
    state = factory.Faker("enum", enum_cls=WorkflowState)
    branch = factory.Faker("word")
    created_at = factory.Faker("date_time")
    updated_at = factory.Faker("date_time")
    event = factory.Faker("enum", enum_cls=WorkflowEvent)
    url = factory.Faker("url")

    class Meta:
        """Declare the model of the factory."""

        model = WorkflowRun


class ProviderFactory(factory.Factory):  # type: ignore
    """Generate a fake provider."""

    id_ = factory.Faker("pyint")
    name = factory.Faker("word")
    git_server = factory.Faker("enum", enum_cls=GitServerType)

    class Meta:
        """Declare the model of the factory."""

        model = Provider
