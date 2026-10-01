import asyncio
import logging
import time

import aiohttp

from config.settings import settings

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """
    Asynchronous GitHub API Client with token-bucket rate limiting,
    automatic backoff, connection pooling, and concurrent telemetry retrieval.
    """

    def __init__(self, token: str | None = None):
        self.base_url = settings.github_api_url.rstrip("/")
        self.token = token or settings.github_token
        self.session: aiohttp.ClientSession | None = None
        self.rate_limit_remaining = 5000 if self.token else 60
        self.rate_limit_reset = time.time()
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def _ensure_session(self):
        if self.session is None or self.session.closed:
            headers = {
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "GitHub-Agent-AI-Octo/2.0",
            }
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            timeout = aiohttp.ClientTimeout(total=settings.request_timeout_seconds)
            connector = aiohttp.TCPConnector(limit=15, enable_cleanup_closed=True)
            self.session = aiohttp.ClientSession(
                headers=headers, timeout=timeout, connector=connector
            )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def _make_request(
        self, endpoint: str, params: dict | None = None, max_retries: int = 3
    ) -> dict:
        """Make an authenticated request with rate limiting and exponential backoff."""
        await self._ensure_session()
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries):
            # Check rate limits
            async with self._lock:
                if self.rate_limit_remaining < 5 and time.time() < self.rate_limit_reset:
                    wait_time = max(1.0, self.rate_limit_reset - time.time() + 1.0)
                    logger.warning(
                        f"GitHub API Rate limit low ({self.rate_limit_remaining} left). Waiting {wait_time:.1f}s..."
                    )
                    await asyncio.sleep(min(wait_time, 60.0))

            try:
                async with self.session.get(url, params=params) as response:
                    # Update rate limit headers
                    if "X-RateLimit-Remaining" in response.headers:
                        self.rate_limit_remaining = int(response.headers["X-RateLimit-Remaining"])
                    if "X-RateLimit-Reset" in response.headers:
                        self.rate_limit_reset = float(response.headers["X-RateLimit-Reset"])

                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return {}
                    elif response.status in (403, 429):
                        # Rate limited
                        retry_after = float(response.headers.get("Retry-After", 2**attempt))
                        logger.warning(
                            f"Rate limited (status {response.status}). Backing off for {retry_after}s (attempt {attempt + 1}/{max_retries})..."
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    else:
                        logger.debug(f"GitHub API request {url} returned status {response.status}")
                        return {}

            except (TimeoutError, aiohttp.ClientError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed request to {url} after {max_retries} attempts: {e}")
                    return {}
                await asyncio.sleep(2**attempt)

        return {}

    async def search_repositories(
        self, keyword: str, max_repos: int | None = None, min_stars: int | None = None
    ) -> list[dict]:
        """Search repositories by keyword sorted by stars and forks."""
        max_count = max_repos or settings.max_repositories
        stars_filter = min_stars if min_stars is not None else settings.min_stars

        query = f"{keyword} stars:>={stars_filter}"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": min(max_count, 100)}

        data = await self._make_request("search/repositories", params=params)
        items = data.get("items", [])
        return items[:max_count]

    async def get_repository(self, owner: str, repo: str) -> dict:
        """Fetch raw repository metadata."""
        return await self._make_request(f"repos/{owner}/{repo}")

    async def get_repository_details(self, repo_data: dict) -> dict:
        """Concurrently fetch repository telemetry (issues, commits, contributors, community profile)."""
        owner = repo_data["owner"]["login"]
        repo_name = repo_data["name"]

        # Fetch in parallel
        issues_task = self.get_issues(owner, repo_name)
        commits_task = self.get_recent_commits(owner, repo_name)
        contributors_task = self.get_contributors(owner, repo_name)
        community_task = self.get_community_profile(owner, repo_name)

        issues, commits, contributors, community = await asyncio.gather(
            issues_task, commits_task, contributors_task, community_task, return_exceptions=True
        )

        return {
            "repo": repo_data,
            "issues": issues if isinstance(issues, list) else [],
            "commits": commits if isinstance(commits, list) else [],
            "contributors": contributors if isinstance(contributors, list) else [],
            "community": community if isinstance(community, dict) else {},
        }

    async def get_issues(
        self, owner: str, repo: str, state: str = "open", per_page: int = 50
    ) -> list[dict]:
        """Fetch recent open issues."""
        params = {"state": state, "per_page": per_page, "sort": "updated", "direction": "desc"}
        res = await self._make_request(f"repos/{owner}/{repo}/issues", params=params)
        if isinstance(res, list):
            # Filter out pull requests which GitHub includes in issues endpoint
            return [i for i in res if "pull_request" not in i]
        return []

    async def get_recent_commits(self, owner: str, repo: str, per_page: int = 30) -> list[dict]:
        """Fetch recent commits in the repository."""
        params = {"per_page": per_page}
        res = await self._make_request(f"repos/{owner}/{repo}/commits", params=params)
        return res if isinstance(res, list) else []

    async def get_contributors(self, owner: str, repo: str, per_page: int = 30) -> list[dict]:
        """Fetch top contributors."""
        params = {"per_page": per_page}
        res = await self._make_request(f"repos/{owner}/{repo}/contributors", params=params)
        return res if isinstance(res, list) else []

    async def get_community_profile(self, owner: str, repo: str) -> dict:
        """Fetch repository community profile (health score, license, contributing docs)."""
        return await self._make_request(f"repos/{owner}/{repo}/community/profile")

    async def check_file_exists(self, owner: str, repo: str, path: str) -> bool:
        """Check if a specific file exists in the repository root or .github folder."""
        # Check root
        data = await self._make_request(f"repos/{owner}/{repo}/contents/{path}")
        if data and "name" in data:
            return True
        # Check inside .github/
        data_github = await self._make_request(f"repos/{owner}/{repo}/contents/.github/{path}")
        return bool(data_github and "name" in data_github)
