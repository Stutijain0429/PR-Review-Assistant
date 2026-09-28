"""
Fetches PR diffs directly from GitHub's API.
Given a PR URL like https://github.com/owner/repo/pull/123,
returns the raw unified diff text.
"""

import os
import re
import requests
from typing import Tuple

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")


def parse_pr_url(pr_url: str) -> Tuple[str, str, int]:
    """
    Extracts (owner, repo, pr_number) from a GitHub PR URL.
    Example: https://github.com/facebook/react/pull/12345
    """
    pattern = r"github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.search(pattern, pr_url)
    if not match:
        raise ValueError(f"Could not parse a valid GitHub PR URL from: {pr_url}")

    owner, repo, pr_number = match.groups()
    return owner, repo, int(pr_number)


def fetch_pr_diff(pr_url: str) -> str:
    """
    Fetches the raw diff text for a given PR URL using GitHub's REST API.
    """
    owner, repo, pr_number = parse_pr_url(pr_url)

    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

    headers = {
        "Accept": "application/vnd.github.v3.diff",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = requests.get(api_url, headers=headers, timeout=15)

    if response.status_code == 404:
        raise ValueError(f"PR not found: {pr_url}. Check the URL and that the repo is public (or your token has access).")
    if response.status_code == 403:
        raise ValueError("GitHub API rate limit exceeded or access forbidden. Check your GITHUB_TOKEN.")
    response.raise_for_status()

    return response.text

def fetch_repo_conventions(pr_url: str) -> str:
    """
    Fetches the repo's README or CONTRIBUTING.md to use as context
    for style/convention-aware reviews. Returns empty string if none found.
    """
    owner, repo, _ = parse_pr_url(pr_url)

    headers = {}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    candidates = ["CONTRIBUTING.md", "CONTRIBUTING.rst", "README.md"]

    for filename in candidates:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{filename}"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            import base64
            content_b64 = response.json().get("content", "")
            try:
                content = base64.b64decode(content_b64).decode("utf-8")
                # Truncate to keep prompt size reasonable
                return content[:3000]
            except Exception:
                continue

    return ""