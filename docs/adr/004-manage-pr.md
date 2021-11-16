Date: 2021-11-16

# Status
<!-- What is the status? Draft, Proposed, Accepted, Rejected, Deprecated or Superseded?
-->
Draft

# Context
<!-- What is the issue that we're seeing that is motivating this decision or change? -->
Making pull requests is cumbersome, you need to:

* Pull latest changes on `master`.
* Create a branch
* Code the changes
* Make one or many meaningful commits
* Push changes
* Open the link of the PR in a browser
* Fill up the title and description
* Wait for the CI to pass
* Merge the pull request
* Checkout locally to master
* Pull the changes
* Optionally make a release

Many of these steps can be automated so that the human interaction is reduced.

# Proposals
<!-- What are the possible solutions to the problem described in the context -->
Have a command line tool that for the repository in the working directory:

* If there are non commited changes it will fail.
* Checks out `master`
* Pull latest changes on `master`.
* Asks the user if it's a feature/fix/ci/... change
* Creates a branch

Once the branch is ready to be merged, another command will:

* Push changes
* Open the PR filling up the details with:
    * The title taken from the branch name
    * The description by semantic understanding the changes
* Wait for the CI to pass. If it doesn't, show the error so that the human can
    fix it, run the same command and it will push the changes and wait again
    until the CI passes.
* If automerge is set, and the CI has passed, it will merge the PR.
* Checkout locally to master
* Pull the changes
* If the PR was marked with the `--release` flag, it will run `make bump`.

# Decision
<!-- What is the change that we're proposing and/or doing? -->

# Consequences
<!-- What becomes easier or more difficult to do because of this change? -->
