#!/usr/bin/env python3
"""
Create (or reuse) a pull request on a Gitea instance using the JSON REST API.

Equivalent to:

    curl -X POST '<url>/api/v1/repos/<owner>/<repo>/pulls?token=<token>' \
      -H 'accept: application/json' \
      -H 'Content-Type: application/json' \
      -d '{"base": "...", "head": "...", "title": "...", "body": "..."}'

except the token is sent as an Authorization header instead of a query
parameter, and the script first checks for an existing open PR on the same
branch to avoid creating duplicates.
"""
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request


def env(name, default=""):
    return os.environ.get(name, default)


def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()


def parse_owner_repo(remote_url):
    """Pull 'owner' and 'repo' out of an http(s) or ssh git remote URL."""
    remote_url = remote_url.strip()
    if remote_url.endswith(".git"):
        remote_url = remote_url[:-4]
    match = re.search(r"[:/]([^/:]+)/([^/]+)$", remote_url)
    if not match:
        raise ValueError(f"Could not parse owner/repo from remote URL: {remote_url}")
    return match.group(1), match.group(2)


def api_request(url, token, method="GET", data=None):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"token {token}",
    }
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            payload = json.loads(raw)
        except Exception:
            payload = raw.decode("utf-8", "replace")
        return e.code, payload


def set_output(name, value):
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output:
        with open(gh_output, "a") as f:
            f.write(f"{name}={value}\n")


def main():
    gitea_url = env("GITEA_URL").rstrip("/")
    token = env("GITEA_TOKEN")
    remote_name = env("GITEA_REMOTE", "origin")
    base = env("PR_BASE")
    branch = env("PR_BRANCH")
    title = env("PR_TITLE")
    body_path = env("PR_BODY_PATH")
    labels_raw = env("PR_LABELS")
    assignees_raw = env("PR_ASSIGNEES")

    if not gitea_url or not token:
        print("::error::'url' and 'token' inputs are required.")
        sys.exit(1)
    if not branch:
        print("::error::'branch' input is required.")
        sys.exit(1)

    # body-path takes precedence over body when both are set.
    if body_path:
        with open(body_path, "r") as f:
            body = f.read()
    else:
        body = env("PR_BODY")

    remote_url = run(["git", "remote", "get-url", remote_name])
    owner, repo = parse_owner_repo(remote_url)
    print(f"Target Gitea repo: {owner}/{repo}")

    api_base = f"{gitea_url}/api/v1/repos/{owner}/{repo}"

    # 1. Check for an existing open PR on this branch to avoid duplicates.
    status, existing = api_request(f"{api_base}/pulls?state=open&limit=50", token)
    if status != 200:
        print(f"::error::Failed to list existing pull requests ({status}): {existing}")
        sys.exit(1)

    for pr in existing or []:
        if pr.get("head", {}).get("ref") == branch:
            print(f"A pull request for branch '{branch}' already exists: {pr['html_url']}")
            set_output("pr-url", pr["html_url"])
            set_output("pr-number", pr["number"])
            return

    # 2. Resolve label names to IDs (Gitea's create-PR endpoint takes label IDs).
    label_ids = []
    if labels_raw:
        status, all_labels = api_request(f"{api_base}/labels?limit=200", token)
        if status != 200:
            print(f"::warning::Could not fetch labels ({status}): {all_labels}")
            all_labels = []
        by_name = {l["name"]: l["id"] for l in (all_labels or [])}
        for name in [l.strip() for l in labels_raw.split(",") if l.strip()]:
            if name in by_name:
                label_ids.append(by_name[name])
            else:
                print(f"::warning::Label '{name}' not found in {owner}/{repo}, skipping.")

    # 3. Build the JSON payload and create the PR.
    payload = {
        "head": branch,
        "title": title,
        "body": body,
    }
    if base:
        payload["base"] = base
    if label_ids:
        payload["labels"] = label_ids
    if assignees_raw:
        payload["assignees"] = [a.strip() for a in assignees_raw.split(",") if a.strip()]

    status, result = api_request(f"{api_base}/pulls", token, method="POST", data=payload)
    if status not in (200, 201):
        print(f"::error::Failed to create pull request ({status}): {result}")
        sys.exit(1)

    print(f"Created pull request: {result['html_url']}")
    set_output("pr-url", result["html_url"])
    set_output("pr-number", result["number"])


if __name__ == "__main__":
    main()
