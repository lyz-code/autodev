"""Tests the service layer."""

import logging
import os
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from git import Repo
from repository_orm import Repository, load_repository
from tests.conftest import commit, latest_commit

from autodev.exceptions import CruftUpdateFailedError
from autodev.model import (
    GitRepository,
    GitRepositoryState,
    Workflow,
    WorkflowRun,
    WorkflowState,
)
from autodev.services import (
    get_cruft_template,
    get_file_path,
    start_cruft_update,
    update_git_repositories,
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

        update_git_repositories(repo, {0: adapter})  # act

        workflows = repo.all(Workflow)
        assert workflows[0].state == WorkflowState.SUCCESS
        assert workflows[1].state == WorkflowState.FAILURE
        assert workflows[2].state == WorkflowState.UNKNOWN
        assert repo.all(GitRepository)[0].state == GitRepositoryState.BROKEN


class TestGetFilePath:
    """Tests for the `get_file_path`."""

    @patch("autodev.services.Path", autospec=True)
    def test_in_current_directory(
        self, mock_path: MagicMock, create_tmp_file: Callable[..., Path]
    ) -> None:
        """
        Given a file in the `cwd`,
        When the `get_file_path` function is invoked without a `starting_path`,
        Then the path to the file is returned
        """
        path_to_file = create_tmp_file(filename="file.txt")
        mock_path.cwd.return_value = path_to_file.parent

        result = get_file_path(filename="file.txt")

        assert result == path_to_file

    def test_in_parent_directory(self, create_tmp_file: Callable[..., Path]) -> None:
        """
        Given a file in the parent of `cwd`,
        When the `get_file_path` function is invoked,
        Then the path to the file is returned
        """
        path_to_file = create_tmp_file(filename="file.txt")
        sub_dir = path_to_file / "sub"

        result = get_file_path(filename="file.txt", starting_path=sub_dir)

        assert result == path_to_file

    def test_not_found(self) -> None:
        """
        Given no in the `cwd` or parent dirs,
        When the `get_file_path` function is invoked,
        Then `None` is returned
        """
        result = get_file_path(filename="file.txt", starting_path=Path("/nowhere"))

        assert result is None

    def test_with_given_path(self, create_tmp_file: Callable[..., Path]) -> None:
        """
        Given a file in a path,
        When the `get_file_path` function is invoked with a `starting_path`,
        Then the path to the file is returned
        """
        path_to_file = create_tmp_file(filename="file.txt")

        result = get_file_path(filename="file.txt", starting_path=path_to_file)

        assert result == path_to_file


class TestGetCruftTemplate:
    """Tests for the `get_cruft_template`."""

    def test_gets_repository_and_commit(self, cruft_json: Path) -> None:
        """
        Given: A .cruft.json file.
        When: function is called
        Then: the repository url and the current commit is returned
        """
        repository = "tests/assets/template_repo"
        commit = "7077aa7dc32e0bacc43780813ea5bfd59b2450b3"

        result = get_cruft_template(cruft_json)

        assert result == (repository, commit)


class TestUpdateCruft:
    """Tests for the updating of a cruft template."""

    def test_update_handles_not_found(self, git_repo: Repo) -> None:
        """
        Given: a working directory without any .cruft.json
        When: start_cruft_update is called
        Then: An error is raised
        """
        os.remove(".cruft.json")
        with pytest.raises(
            FileNotFoundError, match="Could not find the .cruft.json file of the repo."
        ):
            start_cruft_update()

    def test_update_does_nothing_if_repo_is_updated(
        self, git_repo: Repo, caplog: LogCaptureFixture
    ) -> None:
        """
        Given: a repository created with cruft, that is using the latest version of the
            template.
        When: start_cruft_update is called
        Then: an info message is shown that the repository is updated.
        """
        caplog.set_level(logging.INFO)

        start_cruft_update()

        assert (
            "autodev.services",
            logging.INFO,
            "Already in the latest version of the template",
        ) in caplog.record_tuples

    def test_update_raises_error_if_there_are_uncommitted_files_before_the_apply(
        self, git_repo: Repo, template_repo: Repo, caplog: LogCaptureFixture
    ) -> None:
        """
        Given: a repository created with cruft, that is not using the latest version
            but that has uncommitted files
        When: start_cruft_update is called
        Then: an error message is shown that you need to have a clean environment to
            run `update`
        """
        # Make a change in the template
        template_work_dir = Path(template_repo.working_dir)
        readme = template_work_dir / "README.md"
        readme.write_text("template change")
        commit(template_repo, ["README.md"], "update template")
        # Make uncommitted changes in the child repo
        work_dir = Path(git_repo.working_dir)
        readme = work_dir / "README.md"
        readme.write_text("Uncommitted changes")

        with pytest.raises(
            CruftUpdateFailedError,
            match=(
                "Cruft cannot apply updates on an unclean git project. "
                "Please make sure your git working tree is clean before proceeding.\n"
            ),
        ):
            start_cruft_update()

    def test_update_creates_new_branch_if_update_went_right(
        self, git_repo: Repo, template_repo: Repo
    ) -> None:
        """
        Given: a repository created with cruft, that is not using the latest version and
            has a clean state.
        When: start_cruft_update is called
        Then: cruft update is run well, a branch is created, and the template url is
            returned.
        """
        # Make a change in the template
        repo_template_version = latest_commit(template_repo)
        template_work_dir = Path(template_repo.working_dir)
        readme = template_work_dir / "{{cookiecutter.project_name}}/README.md"
        readme.write_text("template change")
        commit(
            template_repo,
            ["{{cookiecutter.project_name}}/README.md"],
            "update template",
        )

        result = start_cruft_update()

        assert (
            git_repo.active_branch.name == f"feat/update-cruft-{repo_template_version}"
        )
        assert result == template_repo.working_dir
        with open(f"{git_repo.working_dir}/README.md", "r") as file_descriptor:
            assert file_descriptor.read() == "template change"

    def test_update_raises_error_if_needs_human_interaction_after_cruft_update(
        self, git_repo: Repo, template_repo: Repo
    ) -> None:
        """
        Given: a repository created with cruft, that is not using the latest version and
            has a clean state, but that when updated it will have conflicts that cruft
            is not able to solve.
        When: start_cruft_update is called
        Then: An error is raised, but the branch is changed
        """
        # Make a change in the template
        repo_template_version = latest_commit(template_repo)
        template_work_dir = Path(template_repo.working_dir)
        readme = template_work_dir / "{{cookiecutter.project_name}}/README.md"
        readme.write_text("template change")
        commit(
            template_repo,
            ["{{cookiecutter.project_name}}/README.md"],
            "update template",
        )
        # Make the same change in the repo so there is a conflict
        repo_work_dir = Path(git_repo.working_dir)
        readme = repo_work_dir / "README.md"
        readme.write_text("template change that introduces conflict")
        commit(git_repo, ["README.md"], "update template")

        with pytest.raises(
            CruftUpdateFailedError,
            match=(
                "The update didn't went smooth, you need to solve the conflicts "
                "yourself, but let me do the commit."
            ),
        ):
            start_cruft_update()

        assert (
            git_repo.active_branch.name == f"feat/update-cruft-{repo_template_version}"
        )

    def test_update_skips_first_update_steps_if_already_in_update_branch(
        self, git_repo: Repo, template_repo: Repo
    ) -> None:
        """
        Given: A repository created with cruft, where update was already run but failed
            but the user already fixed the conflicts, so there are files that have
            changed and the git state is not clean
        When: start_cruft_update is called
        Then: the process ends well.
        """
        # Simulate the branch change done by the first start_cruft_update
        new_branch = git_repo.create_head(
            f"feat/update-cruft-{latest_commit(template_repo)}"
        )
        git_repo.head.reference = new_branch
        # Make a change in the template
        repo_template_version = latest_commit(template_repo)
        template_work_dir = Path(template_repo.working_dir)
        readme = template_work_dir / "README.md"
        readme.write_text("template change")
        commit(template_repo, ["README.md"], "update template")
        # Make a change that simulates that the user has solved the conflicts
        repo_work_dir = Path(git_repo.working_dir)
        readme = repo_work_dir / "README.md"
        readme.write_text("solved conflict change")

        result = start_cruft_update()

        assert result == template_repo.working_dir
