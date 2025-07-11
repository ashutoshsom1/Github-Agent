import asyncio
import aiohttp
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import time
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import settings

class GitHubAPIClient:
    def __init__(self):
        self.base_url = settings.github_api_url
        self.token = settings.github_token
        self.session = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = time.time()
        self._session_created = False
        
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._close_session()
    
    async def _ensure_session(self):
        """Ensure session is created"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            self._session_created = True
    
    async def _close_session(self):
        """Close session if it was created"""
        if self.session and self._session_created:
            await self.session.close()
            self.session = None
            self._session_created = False
    
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with rate limiting"""
        # Ensure session is created
        await self._ensure_session()
        
        if self.rate_limit_remaining < 10 and time.time() < self.rate_limit_reset:
            wait_time = self.rate_limit_reset - time.time()
            print(f"⏳ Rate limit reached. Waiting {wait_time:.1f} seconds...")
            await asyncio.sleep(wait_time)
        
        async with self.session.get(url, params=params) as response:
            # Update rate limit info
            self.rate_limit_remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
            self.rate_limit_reset = int(response.headers.get('X-RateLimit-Reset', time.time()))
            
            if response.status == 200:
                return await response.json()
            elif response.status == 404:
                # File/resource not found - this is expected for some queries
                return {}
            else:
                print(f"❌ API request failed: {response.status} for {url}")
                return {}
    
    async def search_repositories(self, keyword: str, sort: str = "stars") -> List[Dict]:
        """Search for repositories by keyword"""
        url = f"{self.base_url}/search/repositories"
        params = {
            "q": f"{keyword} stars:>{settings.min_stars}",
            "sort": sort,
            "order": "desc",
            "per_page": min(settings.max_repositories, 100)
        }
        
        data = await self._make_request(url, params)
        return data.get('items', [])
    
    async def get_repository_details(self, repo: Dict) -> Dict:
        """Get detailed repository information"""
        owner = repo['owner']['login']
        name = repo['name']
        
        # Basic repo info
        repo_url = f"{self.base_url}/repos/{owner}/{name}"
        repo_data = await self._make_request(repo_url)
        
        # Get additional details
        issues_url = f"{self.base_url}/repos/{owner}/{name}/issues"
        issues_params = {
            "state": "open",
            "labels": "good-first-issue,help-wanted,beginner,easy",
            "per_page": 100
        }
        issues_data = await self._make_request(issues_url, issues_params)
        
        # Get commits (last 3 months)
        since_date = (datetime.now() - timedelta(days=90)).isoformat()
        commits_url = f"{self.base_url}/repos/{owner}/{name}/commits"
        commits_params = {"since": since_date, "per_page": 100}
        commits_data = await self._make_request(commits_url, commits_params)
        
        # Get contributors
        contributors_url = f"{self.base_url}/repos/{owner}/{name}/contributors"
        contributors_data = await self._make_request(contributors_url, {"per_page": 50})
        
        return {
            "repo": repo_data,
            "issues": issues_data if isinstance(issues_data, list) else [],
            "commits": commits_data if isinstance(commits_data, list) else [],
            "contributors": contributors_data if isinstance(contributors_data, list) else []
        }
    
    async def check_file_exists(self, owner: str, repo: str, file_path: str) -> bool:
        """Check if a specific file exists in the repository"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        data = await self._make_request(url)
        
        # Handle both single files and directories
        if isinstance(data, dict):
            return bool(data.get('name'))
        elif isinstance(data, list):
            return len(data) > 0
        else:
            return False
    
    async def get_file_content(self, owner: str, repo: str, file_path: str) -> Optional[str]:
        """Get content of a specific file"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}"
        data = await self._make_request(url)
        
        if data.get('content'):
            import base64
            return base64.b64decode(data['content']).decode('utf-8')
        return None
