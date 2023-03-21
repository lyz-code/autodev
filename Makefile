.DEFAULT_GOAL := test
isort = isort src docs/examples tests
black = black --target-version py37 src docs/examples tests

.PHONY: install
install:
	pdm install
	pre-commit install

.PHONY: update
update:
	@echo "-------------------------"
	@echo "- Updating dependencies -"
	@echo "-------------------------"

	poetry update

	@echo ""

.PHONY: upgrade
upgrade:
	@echo "-------------------------"
	@echo "- Upgrading dependencies -"
	@echo "-------------------------"

	poetryup

.PHONY: format
format:
	@echo "----------------------"
	@echo "- Formating the code -"
	@echo "----------------------"

	$(isort)
	$(black)

	@echo ""

.PHONY: lint
lint:
	@echo "--------------------"
	@echo "- Testing the lint -"
	@echo "--------------------"

	flakehell lint src/ tests/
	$(isort) --check-only --df
	$(black) --check --diff

	@echo ""

.PHONY: mypy
mypy:
	@echo "----------------"
	@echo "- Testing mypy -"
	@echo "----------------"

	mypy src tests

	@echo ""

.PHONY: test
test: test-code test-examples

.PHONY: test-code
test-code:
	@echo "----------------"
	@echo "- Testing code -"
	@echo "----------------"

	pytest --cov-report term-missing --cov src tests ${ARGS}

	@echo ""

.PHONY: test-examples
test-examples:
	@echo "--------------------"
	@echo "- Testing examples -"
	@echo "--------------------"

	@find docs/examples -type f -name '*.py' | xargs -I'{}' sh -c 'python {} >/dev/null 2>&1 || (echo "{} failed" ; exit 1)'

	@echo ""

.PHONY: all
all: lint mypy test security

.PHONY: clean
clean:
	@echo "---------------------------"
	@echo "- Cleaning unwanted files -"
	@echo "---------------------------"

	rm -rf `find . -name __pycache__`
	rm -f `find . -type f -name '*.py[co]' `
	rm -f `find . -type f -name '*.rej' `
	rm -rf `find . -type d -name '*.egg-info' `
	rm -f `find . -type f -name '*~' `
	rm -f `find . -type f -name '.*~' `
	rm -rf .cache
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -f .coverage
	rm -f .coverage.*
	rm -rf build
	rm -rf dist
	rm -f src/*.c pydantic/*.so
	rm -rf site
	rm -rf docs/_build
	rm -rf docs/.changelog.md docs/.version.md docs/.tmp_schema_mappings.html
	rm -rf codecov.sh
	rm -rf coverage.xml

	@echo ""

.PHONY: docs
docs: test-examples
	@echo "-------------------------"
	@echo "- Serving documentation -"
	@echo "-------------------------"

	mkdocs serve

	@echo ""

.PHONY: bump
bump: pull-master bump-version build-package upload-pypi clean

.PHONY: pull-master
pull-master:
	@echo "------------------------"
	@echo "- Updating repository  -"
	@echo "------------------------"

	git checkout master
	git pull

	@echo ""

.PHONY: build-package
build-package: clean
	@echo "------------------------"
	@echo "- Building the package -"
	@echo "------------------------"

	poetry build

	@echo ""

.PHONY: build-docs
build-docs: test-examples
	@echo "--------------------------"
	@echo "- Building documentation -"
	@echo "--------------------------"

	mkdocs build

	@echo ""

.PHONY: upload-pypi
upload-pypi:
	@echo "-----------------------------"
	@echo "- Uploading package to pypi -"
	@echo "-----------------------------"

	poetry publish

	@echo ""

.PHONY: upload-testing-pypi
upload-testing-pypi:
	@echo "-------------------------------------"
	@echo "- Uploading package to pypi testing -"
	@echo "-------------------------------------"

	poetry publish -r test-pypi

	@echo ""

.PHONY: bump-version
bump-version:
	@echo "---------------------------"
	@echo "- Bumping program version -"
	@echo "---------------------------"

	cz bump --changelog --no-verify
	git push
	git push --tags

	@echo ""

.PHONY: security
security:
	@echo "--------------------"
	@echo "- Testing security -"
	@echo "--------------------"

	safety check
	@echo ""
	bandit -r src

	@echo ""

.PHONY: version
version:
	@python -c "import autodev.version; print(autodev.version.version_info())"
