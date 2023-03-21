"""Store the classes and fixtures used throughout the tests."""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, List

import pytest
from _pytest.fixtures import SubRequest
from cruft._commands import create as create_cruft
from dateutil import tz
from git import Actor, Repo
from py._path.local import LocalPath


@pytest.fixture(name="create_tmp_file")
def create_tmp_file_fixture(tmp_path: Path) -> Callable[..., Path]:
    """Fixture for creating a temporary file."""

    def _create_tmp_file(content: str = "", filename: str = "file.txt") -> Path:
        tmp_file = tmp_path / filename
        tmp_file.write_text(content)
        return tmp_file

    return _create_tmp_file


@pytest.fixture(name="cruft_json")
def cruft_json_(tmpdir: LocalPath) -> Path:
    """Create a cruft.json file and change the working dir."""
    os.chdir(tmpdir)

    repository = "tests/assets/template_repo"
    commit = "7077aa7dc32e0bacc43780813ea5bfd59b2450b3"
    cruft_file = tmpdir / ".cruft.json"
    with open(cruft_file, "w+") as file_descriptor:
        file_descriptor.write(
            json.dumps(
                {
                    "template": repository,
                    "commit": commit,
                }
            )
        )

    return cruft_file


@pytest.fixture(name="change_test_dir")
def change_test_dir_(request: SubRequest) -> Any:
    os.chdir(request.fspath.dirname)
    yield
    os.chdir(request.config.invocation_dir)


@pytest.fixture(name="git_repo")
def git_repo_(tmpdir: LocalPath, template_repo: Repo, change_test_dir: None) -> Repo:
    """Initialize a git repository initialized with cruft.

    Args:
        tmpdir: Pytest fixture that creates a temporal directory
    """
    repo_path = tmpdir / "repo"
    temp_cruft_dir = create_cruft(
        template_git_url=template_repo.working_dir,
        output_dir=tmpdir,
        extra_context={"project_name": "repo"},
    )
    # shutil.copy(temp_cruft_dir / ".cruft.json", repo_path / ".cruft.json")

    os.chdir(repo_path)

    repo = Repo.init(repo_path)
    commit(repo, ["README.md", ".cruft.json"], "Initial skeleton")

    return repo


@pytest.fixture(name="template_repo")
def template_repo_(tmpdir: LocalPath) -> Repo:
    """Initialize the template repository.

    Args:
        tmpdir: Pytest fixture that creates a temporal directory
    """
    repo_path = tmpdir / "template"

    shutil.copytree("tests/assets/template_repo", repo_path)

    repo = Repo.init(repo_path)

    commit(
        repo, ["cookiecutter.json", "{{cookiecutter.project_name}}"], "Initial skeleton"
    )

    return repo


def commit(repo: Repo, files_to_add: List[str], commit_message: str) -> None:
    """Make a commit."""
    index = repo.index
    author = Actor("An author", "author@example.com")
    committer = Actor("A committer", "committer@example.com")

    commit_date = datetime(2021, 2, 1, 12, tzinfo=tz.tzlocal())
    index.add(files_to_add)
    index.commit(
        commit_message,
        author=author,
        committer=committer,
        author_date=str(commit_date),
        commit_date=str(commit_date),
    )


def latest_commit(repo: Repo) -> str:
    """Get the latest commit id of a repo."""
    return repo.head.object.hexsha
