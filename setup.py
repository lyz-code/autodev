"""Python package building configuration."""

import re
from glob import glob
from os.path import basename, splitext

from setuptools import find_packages, setup
import logging
import os
import shutil
from setuptools.command.install import install
from setuptools.command.egg_info import egg_info


log = logging.getLogger(__name__)

# Avoid loading the package to extract the version
with open("src/autodev/version.py") as fp:
    version_match = re.search(r'__version__ = "(?P<version>.*)"', fp.read())
    if version_match is None:
        raise ValueError("The version is not specified in the version.py file.")
    version = version_match["version"]


class PostInstallCommand(install):  # type: ignore
    """Post-installation for installation mode."""

    def run(self) -> None:
        """Create required directories and files."""
        install.run(self)

        try:
            data_directory = os.path.expanduser("~/.local/share/autodev")
            os.makedirs(data_directory)
            log.info("Data directory created")
        except FileExistsError:
            log.info("Data directory already exits")

        config_path = os.path.join(data_directory, "config.yaml")
        if os.path.isfile(config_path) and os.access(config_path, os.R_OK):
            log.info(
                "Configuration file already exists, check the documentation "
                "for the new version changes."
            )
        else:
            shutil.copyfile("assets/config.yaml", config_path)
            log.info("Copied default configuration template")


class PostEggInfoCommand(egg_info):  # type: ignore
    """Post-installation for egg_info mode."""

    def run(self) -> None:
        """Create required directories and files."""
        egg_info.run(self)


with open("README.md", "r") as readme_file:
    readme = readme_file.read()

setup(
    name="autodev",
    version=version,
    description="Command line tool to automate development operations",
    author="Lyz",
    author_email="lyz-code-security-advisories@riseup.net",
    license="GNU General Public License v3",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/lyz-code/autodev",
    packages=find_packages("src"),
    package_dir={"": "src"},
    package_data={"autodev": ["py.typed"]},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Utilities",
        "Natural Language :: English",
    ],
    entry_points="""
        [console_scripts]
        autodev=autodev.entrypoints.cli:cli
    """,
    cmdclass={"install": PostInstallCommand, "egg_info": PostEggInfoCommand},
    install_requires=[
        "Click",
        "ruamel.yaml",
    ],
)
