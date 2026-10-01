from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from github_agent.analyzer import RepositoryAnalyzer
from github_agent.models import ContributionStatus


@pytest.mark.asyncio
async def test_analyzer_scoring_actively_accepting():
    mock_api = MagicMock()
    mock_api.check_file_exists = AsyncMock(return_value=True)

    now = datetime.now(UTC).isoformat()
    repo_data = {
        "name": "awesome-project",
        "full_name": "org/awesome-project",
        "description": "Production repo",
        "html_url": "https://github.com/org/awesome-project",
        "stargazers_count": 5000,
        "forks_count": 800,
        "language": "Python",
        "pushed_at": now,
        "open_issues_count": 25,
        "owner": {"login": "org"},
        "license": {"spdx_id": "Apache-2.0"},
        "archived": False,
        "size": 50000,
        "topics": ["ai", "machine-learning"],
    }

    issues = [
        {
            "number": 1,
            "title": "Good first issue",
            "labels": [{"name": "good-first-issue"}],
            "html_url": "https://github.com/org/awesome-project/issues/1",
            "comments": 2,
        },
        {
            "number": 2,
            "title": "Documentation fix",
            "labels": [{"name": "help-wanted"}],
            "html_url": "https://github.com/org/awesome-project/issues/2",
            "comments": 0,
        },
    ]
    commits = [{"sha": f"commit_{i}"} for i in range(16)]
    contributors = [{"login": f"user_{i}"} for i in range(10)]
    community = {
        "files": {
            "contributing": {"url": "https://..."},
            "code_of_conduct": {"url": "https://..."},
            "issue_template": {"url": "https://..."},
            "pull_request_template": {"url": "https://..."},
        }
    }

    mock_api.get_repository_details = AsyncMock(
        return_value={
            "repo": repo_data,
            "issues": issues,
            "commits": commits,
            "contributors": contributors,
            "community": community,
        }
    )

    analyzer = RepositoryAnalyzer(api_client=mock_api, enable_ai=False)
    analysis = await analyzer.analyze_repository(repo_data)

    assert analysis.name == "awesome-project"
    assert analysis.contribution_score >= 70.0
    assert analysis.contribution_status == ContributionStatus.ACTIVELY_ACCEPTING
    assert analysis.good_first_issues >= 1
    assert len(analysis.opportunities) >= 1


@pytest.mark.asyncio
async def test_analyzer_archived_repository():
    mock_api = MagicMock()
    mock_api.check_file_exists = AsyncMock(return_value=False)

    old_date = (datetime.now(UTC) - timedelta(days=250)).isoformat()
    repo_data = {
        "name": "abandoned-lib",
        "full_name": "user/abandoned-lib",
        "description": "Old repo",
        "html_url": "https://github.com/user/abandoned-lib",
        "stargazers_count": 200,
        "forks_count": 10,
        "language": "JavaScript",
        "pushed_at": old_date,
        "open_issues_count": 100,
        "owner": {"login": "user"},
        "license": None,
        "archived": True,
        "size": 5000,
        "topics": [],
    }

    mock_api.get_repository_details = AsyncMock(
        return_value={
            "repo": repo_data,
            "issues": [],
            "commits": [],
            "contributors": [],
            "community": {},
        }
    )

    analyzer = RepositoryAnalyzer(api_client=mock_api, enable_ai=False)
    analysis = await analyzer.analyze_repository(repo_data)

    assert analysis.contribution_status == ContributionStatus.ARCHIVED_INACTIVE
    assert analysis.contribution_score < 40.0
