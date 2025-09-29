# gitea-pr
Create a new PR on Gitea using Actions. It's designed to streamline workflows where changes made in a GitHub repository need to be reflected in a Gitea repository.

**Note:** This action is designed to run on **Linux x64** runners *only*.

## Features

*   Creates a pull request on a Gitea instance.
*   Uses a Personal Access Token (PAT) for authentication.
*   Sets the PR title and body based on the commit message (or custom values).
*   Assigns a user to the pull request.
*   Applies a specified label to the created PR.
*   Checks for existing pull requests for the same branch to avoid duplicates.
*   Uses `tea` CLI, default version is `0.9.2`

## Usage

```yaml
name: Create Gitea Pull Request

on:
  push:
    branches:
      - your-branch  # Trigger on pushes to your branch

jobs:
  create-pr:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      # ... (Your build/test steps here) ...

      - name: Create Gitea PR
        uses: infinilabs/gitea-pr@v0
        with:
          url: ${{ secrets.GITEA_URL }}       # Your Gitea instance URL
          token: ${{ secrets.GITEA_TOKEN }}   # Your Gitea Personal Access Token
          path: ${{ github.workspace }}          # Optional: Path to the repository (defaults to workspace root)
          commit-message: 'Updated from GitHub Actions'  # Optional: Custom commit message
          committer: 'GitHub Actions <actions@github.com>' # Optional: Custom committer
          author: '${{ github.actor }} <${{ github.actor_id }}+${{ github.actor }}@users.noreply.github.com>' # Optional: Custom author
          signoff: 'false'                             # Optional: Add Signed-off-by line (default: false)
          base: 'main'                                # The target branch in Gitea (default: main or master, according to Gitea config)
          branch: 'feature/my-feature'                 # The source branch for the PR (defaults to a generated branch name)
          title: 'My Awesome Pull Request'               # Optional: Custom PR title
          body: 'This PR was created automatically.'       # Optional: Custom PR body
          pr-label: 'your-label'                         # Optional, add label to your PR
          assignee: 'your-gitea-username'        # Optional, Assign user to your PR
          tea-version: '0.9.2'            # Optional: Specify a different tea version, default value '0.9.2'
```

## Inputs

| Input                    | Data type | Description                                                                                                                                                                                            | Required | Default                                                                                                                                               |
| ------------------------ | --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `url`                    | String    | URL to the Gitea instance.                                                                                                                                                                         | **Yes**  |                                                                                                                                                     |
| `token`                  | String    | Personal access token (PAT) for the Gitea instance.  This should be stored as a GitHub secret.                                                                                                        | **Yes**  |                                                                                                                                                     |
| `path`                   | String    | Relative path under `$GITHUB_WORKSPACE` to the repository. Defaults to `$GITHUB_WORKSPACE`.                                                                                                              | No       | `$GITHUB_WORKSPACE`                                                                                                                                    |
| `commit-message`         | String    | The message to use when committing changes.                                                                                                                                                           | No       | `'[create-pull-request] automated change'`                                                                                                              |
| `committer`              | String    | The committer name and email address in the format `Display Name <email@address.com>`. Defaults to the GitHub Actions bot user.                                                                    | No       | `'github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>'`                                                                      |
| `author`                 | String    | The author name and email address in the format `Display Name <email@address.com>`. Defaults to the user who triggered the workflow run.                                                               | No       | `${{ github.actor }} <${{ github.actor_id }}+${{ github.actor }}@users.noreply.github.com>`                                                          |
| `signoff`               | String     | Add `Signed-off-by` line by the committer at the end of the commit log message.                                                                                                                       | No       | `'false'`                                                                                                                                               |
| `base`                   | String    | The pull request base branch (the branch you want to merge *into*).  Defaults to the default branch of the Gitea repository (usually `main` or `master`).                                          | No       |                                                                                                                                                     |
| `branch`                | String   | The pull request branch name (the branch containing the changes you want to merge).                                               | No      |  `'create-pull-request/patch'`                                                                   |
| `title`                  | String    | The title of the pull request.                                                                                                                                                                      | No       | `'Changes by create-pull-request action'`                                                                                                              |
| `body`                   | String    | The body of the pull request.                                                                                                                                                                      | No       | `'Automated changes by actions'`                                                                                                                   |
|`body-path` | String | Path to file that contains the pull request body. Takes precedence over `body`. | No | |
| `pr-label`             | String     | Comma-separated list of labels to add to the pull request.                                                                                                                                             | No       |                                                                                                                                                     |
|`assignee`| String     |  Gitea username to assign to the pull request.                                                  | No       ||
| `tea-version`            | String    | The version of the `tea` CLI to use.                                                                                                                                                                   | **Yes**  | `0.9.2`                                                                                                                                          |

## Prerequisites

*   **Gitea Personal Access Token (PAT):** You need a Gitea PAT with the necessary permissions (`repo` scope, or at least `repo:status`, `repo:contents`, `repo:pulls`, and `write:repo_hooks` if you want to trigger Gitea CI).  Create this token in your Gitea user settings.
*   **GitHub Secrets:** Store your Gitea PAT as a secret in your GitHub repository settings (e.g., `GITEA_TOKEN`).  Also store your Gitea instance URL as a secret (e.g. `GITEA_URL`)
* **`tea` CLI:** This action relies on the `tea` CLI tool being installed. It will install version 0.9.2 by default.  You can override this with the `tea-version` input.

## How it Works

1.  **Checks for Existing PR:** The action first checks if a pull request already exists for the current branch to avoid creating duplicates.
2.  **Installs `tea` (if necessary):** The action downloads and installs a specific version of `tea` (0.9.2 by default), if not already cached in `/opt/hostedtoolcache/bin`.
3.  **Logs in to Gitea:**  It uses the provided Gitea URL and token to authenticate with the Gitea instance using `tea login add`.
4.  **Creates the Pull Request:** If no existing PR is found, it uses `tea pr create` to create a new pull request with the specified title, body, base branch, and head branch.  It also applies the provided label and assignee, if specified.
5.  **Skips if PR Exists:** If a PR already exists for the branch, the action will output an error message and skip the PR creation step.