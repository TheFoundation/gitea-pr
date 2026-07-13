# gitea-pr

Create a new PR on Gitea using Actions. Designed to streamline workflows where
changes made in a GitHub repository need to be reflected in a Gitea repository.

**Note:** This action runs on **Linux** runners only.

## Features

- Creates a pull request on a Gitea instance by POSTing JSON directly to the
  Gitea REST API (`/repos/{owner}/{repo}/pulls`) — no `tea` CLI, no binary to
  install or cache.
- Uses a Personal Access Token (PAT) for authentication, sent as an
  `Authorization: token <PAT>` header.
- Sets the PR title and body based on the commit message (or custom values).
- Assigns users and applies labels to the created PR.
- Checks for an existing open pull request on the same branch to avoid
  duplicates.

## How it works

1. **Commit & push:** If there are local changes in `path`, they're committed
   with the given `author`/`committer` (and optional `Signed-off-by` line),
   then pushed to `branch` on the Gitea `remote`.
2. **Resolve owner/repo:** The script reads `git remote get-url <remote>` and
   parses the Gitea `owner/repo` from it — no separate input needed.
3. **Check for an existing PR:** `GET /repos/{owner}/{repo}/pulls?state=open`
   — if one already targets `branch`, its URL/number are returned and no new
   PR is created.
4. **Create the PR:** otherwise, a single JSON POST is made:

   ```
   POST {url}/api/v1/repos/{owner}/{repo}/pulls
   Authorization: token <PAT>
   Content-Type: application/json

   {
     "base": "main",
     "head": "content",
     "title": "first pr",
     "body": "This is a PR!"
   }
   ```

   (`labels` and `assignees` are added to the payload when `pr-label` /
   `assignee` are set — label names are resolved to Gitea label IDs first.)

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
        uses: actions/checkout@v4

      # ... (Your build/test steps here) ...

      - name: Create Gitea PR
        uses: thefoundation/gitea-pr@v1
        with:
          url: ${{ secrets.GITEA_URL }}       # Your Gitea instance URL
          token: ${{ secrets.GITEA_TOKEN }}   # Your Gitea Personal Access Token
          path: ${{ github.workspace }}       # Optional: path to the repository
          remote: 'origin'                    # Optional: git remote pointing at Gitea
          commit-message: 'Updated from GitHub Actions'
          committer: 'GitHub Actions <actions@github.com>'
          author: '${{ github.actor }} <${{ github.actor_id }}+${{ github.actor }}@users.noreply.github.com>'
          signoff: 'false'
          base: 'main'
          branch: 'feature/my-feature'
          title: 'My Awesome Pull Request'
          body: 'This PR was created automatically.'
          pr-label: 'your-label'
          assignee: 'your-gitea-username'
```

## Inputs

| Input            | Data type | Description                                                                                             | Required | Default                                                                                     |
| ---------------- | --------- | --------------------------------------------------------------------------------------------------------- | -------- | -------------------------------------------------------------------------------------------- |
| `url`            | String    | URL to the Gitea instance.                                                                               | **Yes**  |                                                                                              |
| `token`          | String    | Gitea PAT. Store as a GitHub secret.                                                                     | **Yes**  |                                                                                              |
| `path`           | String    | Relative path under `$GITHUB_WORKSPACE` to the repository.                                               | No       | `$GITHUB_WORKSPACE`                                                                          |
| `remote`         | String    | Name of the git remote pointing at the Gitea repository.                                                 | No       | `origin`                                                                                     |
| `commit-message` | String    | Commit message used when committing local changes.                                                       | No       | `'[create-pull-request] automated change'`                                                   |
| `committer`      | String    | Committer name/email, `Display Name <email@address.com>`.                                                | No       | `'github-actions[bot] <41898282+github-actions[bot]@users.noreply.github.com>'`              |
| `author`         | String    | Author name/email, `Display Name <email@address.com>`.                                                   | No       | `${{ github.actor }} <${{ github.actor_id }}+${{ github.actor }}@users.noreply.github.com>` |
| `signoff`        | String    | Add `Signed-off-by` line.                                                                                 | No       | `'false'`                                                                                    |
| `base`           | String    | PR base branch. Defaults to the Gitea repo's default branch if omitted.                                  | No       |                                                                                               |
| `branch`         | String    | PR head/source branch.                                                                                   | No       | `'create-pull-request/patch'`                                                                |
| `title`          | String    | PR title.                                                                                                 | No       | `'Changes by create-pull-request action'`                                                    |
| `body`           | String    | PR body.                                                                                                  | No       | `'Automated changes by actions'`                                                             |
| `body-path`      | String    | Path to a file containing the PR body. Takes precedence over `body`.                                     | No       |                                                                                               |
| `pr-label`       | String    | Comma-separated list of labels to add.                                                                    | No       |                                                                                               |
| `assignee`       | String    | Comma-separated list of Gitea usernames to assign.                                                        | No       |                                                                                               |

## Outputs

| Output       | Description                                        |
| ------------ | --------------------------------------------------- |
| `pr-url`     | URL of the created (or already-existing) pull request. |
| `pr-number`  | Number of the created (or already-existing) pull request. |

## Prerequisites

- **Gitea Personal Access Token (PAT):** needs `repo` scope (or at least
  `repo:status`, `repo:contents`, and `repo:pulls`).
- **GitHub Secrets:** store the PAT and Gitea instance URL as secrets (e.g.
  `GITEA_TOKEN`, `GITEA_URL`).
- **Python 3:** installed automatically by the action via `actions/setup-python`.
