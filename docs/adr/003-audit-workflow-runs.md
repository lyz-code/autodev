Date: 2021-11-16

# Status
<!-- What is the status? Draft, Proposed, Accepted, Rejected, Deprecated or Superseded?
-->
Draft

# Context
<!-- What is the issue that we're seeing that is motivating this decision or change? -->
When you maintain many repositories that run workflows with a cronjob it's easy
to get your mailbox filled up with failed jobs. Sometimes the issues get solved
by themselves in the next days as the underlying dependencies fix the issues
that broke the pipeline, so it makes sense to leave some jobs broken for some
days before acting upon them.

# Proposals
<!-- What are the possible solutions to the problem described in the context -->
Monitor the pipeline jobs of the maintained repositories, and given the desired
logic for each one, mark them as in need of review so that a human can fix them.

We can show it in a tui dashboard.

The repositories to monitor will be defined in the configuration file. We'll
have two kinds of logic to mark a repository as in need of maintenance:

* If any build originated on a `master` branch is marked as failed.
* If a scheduled workflow is marked as failed for a week.

To gather that information we need:

* The models of `Repository` and `Workflow`.
* A service that gathers the status of the workflows of the repositories, and
    saves it into the database.
* A service that checks the `Workflow` status, and marks the state of the
    `Repository`.
* A command line tool that shows the information of the Repositories

# Decision
<!-- What is the change that we're proposing and/or doing? -->

# Consequences
<!-- What becomes easier or more difficult to do because of this change? -->
