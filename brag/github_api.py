"""Read repo facts from the GitHub API, with a shallow clone only for README text."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request

API = "https://api.github.com"
_NAME = re.compile(r"^[A-Za-z0-9_.-]+$")
_BRANCH = re.compile(r"^[A-Za-z0-9_./-]+$")


class GitHubError(RuntimeError):
    pass


def parse_repo(spec: str) -> tuple[str, str, str | None]:
    """Return owner, repo, optional branch from owner/repo, owner/repo@branch, or a GitHub URL."""
    text = spec.strip().rstrip("/")
    text = re.sub(r"\.git$", "", text)
    url = re.match(
        r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?(?:/.*)?$",
        text,
    )
    if url:
        owner, repo, branch = url.group(1), url.group(2), url.group(3)
    else:
        slug = re.match(r"([^/\s]+)/([^@\s]+)(?:@(\S+))?$", text)
        if not slug:
            raise GitHubError(
                f"expected owner/repo, owner/repo@branch, or a github.com URL, got {spec!r}"
            )
        owner, repo, branch = slug.group(1), slug.group(2), slug.group(3)
    if not _NAME.match(owner) or not _NAME.match(repo):
        raise GitHubError(f"unsupported owner/repo characters in {spec!r}")
    if branch is not None and (not branch or not _BRANCH.match(branch) or branch.startswith("-")):
        raise GitHubError(f"unsupported branch name in {spec!r}")
    return owner, repo, branch


def link_last_page(link_header: str | None) -> int | None:
    """Page number of rel=last, which equals the item count when per_page=1."""
    if not link_header:
        return None
    for part in link_header.split(","):
        if 'rel="last"' not in part:
            continue
        match = re.search(r"[?&]page=(\d+)", part)
        if match:
            return int(match.group(1))
    return None


def auth_token() -> str | None:
    for key in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    try:
        out = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    token = out.stdout.strip()
    return token or None


def _request(url: str, token: str | None, accept: str) -> tuple[int, bytes, dict[str, str]]:
    headers = {
        "Accept": accept,
        "User-Agent": "brag-local",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, resp.read(), {k.lower(): v for k, v in resp.headers.items()}
    except urllib.error.HTTPError as err:
        return err.code, err.read(), {k.lower(): v for k, v in err.headers.items()}


def _json_request(url: str, token: str | None) -> tuple[int, object, dict[str, str]]:
    status, body, headers = _request(url, token, "application/vnd.github+json")
    if not body:
        return status, None, headers
    try:
        return status, json.loads(body.decode("utf-8")), headers
    except json.JSONDecodeError as err:
        raise GitHubError(f"GitHub returned non-JSON from {url}") from err


def _count_list(url: str, token: str | None, what: str) -> int:
    status, payload, headers = _json_request(url, token)
    if status == 409:
        return 0
    if status != 200:
        raise GitHubError(f"GitHub {status} while counting {what}")
    if not isinstance(payload, list):
        raise GitHubError(f"unexpected {what} payload")
    if not payload:
        return 0
    last = link_last_page(headers.get("link"))
    if last is not None:
        return last
    link = headers.get("link") or ""
    if 'rel="next"' not in link:
        return len(payload)
    raise GitHubError(f"GitHub did not report a total for {what}")


def _readme(owner: str, repo: str, branch: str | None, token: str | None) -> str:
    query = f"?ref={urllib.parse.quote(branch)}" if branch else ""
    url = f"{API}/repos/{owner}/{repo}/readme{query}"
    status, body, _headers = _request(url, token, "application/vnd.github.raw")
    if status == 200:
        return body.decode("utf-8", errors="replace")
    if status == 404:
        return _readme_from_clone(owner, repo, branch)
    raise GitHubError(f"GitHub {status} while reading README for {owner}/{repo}")


def _readme_from_clone(owner: str, repo: str, branch: str | None) -> str:
    dest = tempfile.mkdtemp(prefix="brag-clone-")
    try:
        cmd = ["git", "clone", "--depth", "1", "--quiet"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([f"https://github.com/{owner}/{repo}.git", dest])
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            tail = detail[-1] if detail else "clone failed"
            raise GitHubError(f"could not read {owner}/{repo}: {tail}")
        for name in ("README.md", "README.rst", "README.txt", "readme.md", "Readme.md"):
            path = os.path.join(dest, name)
            if os.path.isfile(path):
                with open(path, encoding="utf-8", errors="replace") as handle:
                    return handle.read()
        return ""
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def gather(spec: str, token: str | None = None) -> dict:
    """Fetch name, description, language, PR count, commit count, and README."""
    owner, repo, branch = parse_repo(spec)
    token = auth_token() if token is None else token
    status, payload, _headers = _json_request(f"{API}/repos/{owner}/{repo}", token)
    if status == 404:
        raise GitHubError(
            f"{owner}/{repo} was not found. Private repos need `gh auth login` "
            "or GH_TOKEN with access to that repo."
        )
    if status != 200 or not isinstance(payload, dict):
        raise GitHubError(f"GitHub {status} while reading {owner}/{repo}")
    resolved = branch or payload.get("default_branch") or "main"
    pulls = f"{API}/repos/{owner}/{repo}/pulls?state=all&per_page=1"
    commits = (
        f"{API}/repos/{owner}/{repo}/commits?per_page=1&sha="
        + urllib.parse.quote(resolved)
    )
    pr_count = _count_list(pulls, token, f"pull requests on {owner}/{repo}")
    commit_count = _count_list(commits, token, f"commits on {owner}/{repo}@{resolved}")
    readme = _readme(owner, repo, resolved if branch else None, token)
    return {
        "owner": owner,
        "repo": repo,
        "branch": resolved,
        "url": f"https://github.com/{owner}/{repo}",
        "description": payload.get("description") or "",
        "language": payload.get("language") or "",
        "pr_count": pr_count,
        "commit_count": commit_count,
        "readme": readme,
    }
