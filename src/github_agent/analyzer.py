from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from github_agent.api_client import GitHubAPIClient

class ContributionStatus(Enum):
    ACTIVELY_ACCEPTING = "actively_accepting"
    LIMITED_SCOPE = "limited_scope"
    NOT_ACCEPTING = "not_accepting"
    ARCHIVED_INACTIVE = "archived_inactive"

@dataclass
class RepositoryAnalysis:
    name: str
    full_name: str
    description: str
    url: str
    stars: int
    forks: int
    language: str
    license: Optional[str]
    contribution_status: ContributionStatus
    contribution_score: float
    last_activity: datetime
    open_issues: int
    good_first_issues: int
    help_wanted_issues: int
    recent_commits: int
    contributors_count: int
    has_contributing_guide: bool
    has_code_of_conduct: bool
    has_issue_templates: bool
    has_pr_templates: bool
    response_time_estimate: str
    tech_stack: List[str]
    setup_complexity: str
    maintainer_activity: str

class RepositoryAnalyzer:
    def __init__(self):
        self.api_client = GitHubAPIClient()
    
    async def analyze_repository(self, repo_data: Dict) -> RepositoryAnalysis:
        """Analyze a repository for contribution readiness"""
        
        # Ensure API client session is ready
        await self.api_client._ensure_session()
        
        try:
            # Get detailed repository information
            details = await self.api_client.get_repository_details(repo_data)
            repo = details["repo"]
            issues = details["issues"]
            commits = details["commits"]
            contributors = details["contributors"]
            
            # Analyze contribution indicators
            analysis = await self._perform_analysis(repo, issues, commits, contributors)
            
            return analysis
        finally:
            # Clean up session
            await self.api_client._close_session()
    
    async def _perform_analysis(self, repo: Dict, issues: List, commits: List, contributors: List) -> RepositoryAnalysis:
        """Perform comprehensive repository analysis"""
        
        owner = repo['owner']['login']
        name = repo['name']
        
        # Check for contribution files
        await self.api_client._ensure_session()
        has_contributing = await self.api_client.check_file_exists(owner, name, "CONTRIBUTING.md")
        has_coc = await self.api_client.check_file_exists(owner, name, "CODE_OF_CONDUCT.md")
        has_issue_template = await self.api_client.check_file_exists(owner, name, ".github/ISSUE_TEMPLATE")
        has_pr_template = await self.api_client.check_file_exists(owner, name, ".github/PULL_REQUEST_TEMPLATE.md")
        
        # Analyze issues
        good_first_issues = self._count_labeled_issues(issues, ["good-first-issue", "good first issue"])
        help_wanted_issues = self._count_labeled_issues(issues, ["help-wanted", "help wanted"])
        
        # Calculate contribution score
        contribution_score = self._calculate_contribution_score(
            repo, issues, commits, contributors, has_contributing, 
            good_first_issues, help_wanted_issues
        )
        
        # Determine contribution status
        contribution_status = self._determine_contribution_status(
            repo, contribution_score, commits, has_contributing
        )
        
        # Analyze tech stack
        tech_stack = self._analyze_tech_stack(repo)
        
        # Estimate response time based on recent activity
        response_time = self._estimate_response_time(commits, issues)
        
        # Assess setup complexity
        setup_complexity = self._assess_setup_complexity(repo, tech_stack)
        
        # Analyze maintainer activity
        maintainer_activity = self._analyze_maintainer_activity(commits, contributors)
        
        return RepositoryAnalysis(
            name=repo.get('name', ''),
            full_name=repo.get('full_name', ''),
            description=repo.get('description', ''),
            url=repo.get('html_url', ''),
            stars=repo.get('stargazers_count', 0),
            forks=repo.get('forks_count', 0),
            language=repo.get('language', 'Unknown'),
            license=repo.get('license', {}).get('name') if repo.get('license') else None,
            contribution_status=contribution_status,
            contribution_score=contribution_score,
            last_activity=self._parse_datetime(repo.get('updated_at', '')),
            open_issues=repo.get('open_issues_count', 0),
            good_first_issues=good_first_issues,
            help_wanted_issues=help_wanted_issues,
            recent_commits=len(commits),
            contributors_count=len(contributors),
            has_contributing_guide=has_contributing,
            has_code_of_conduct=has_coc,
            has_issue_templates=has_issue_template,
            has_pr_templates=has_pr_template,
            response_time_estimate=response_time,
            tech_stack=tech_stack,
            setup_complexity=setup_complexity,
            maintainer_activity=maintainer_activity
        )
    
    def _count_labeled_issues(self, issues: List, labels: List[str]) -> int:
        """Count issues with specific labels"""
        count = 0
        for issue in issues:
            issue_labels = [label.get('name', '').lower() for label in issue.get('labels', [])]
            if any(label.lower() in issue_labels for label in labels):
                count += 1
        return count
    
    def _calculate_contribution_score(self, repo: Dict, issues: List, commits: List, 
                                    contributors: List, has_contributing: bool,
                                    good_first_issues: int, help_wanted_issues: int) -> float:
        """Calculate a contribution readiness score (0-100)"""
        score = 0
        
        # Base score for being public and not archived
        if not repo.get('archived', True):
            score += 20
        
        # Documentation score
        if has_contributing:
            score += 15
        if repo.get('description'):
            score += 5
        if repo.get('homepage'):
            score += 5
        
        # Activity score
        if len(commits) > 10:
            score += 15
        elif len(commits) > 5:
            score += 10
        elif len(commits) > 0:
            score += 5
        
        # Community score
        if good_first_issues > 0:
            score += 10
        if help_wanted_issues > 0:
            score += 10
        if len(contributors) > 5:
            score += 10
        elif len(contributors) > 1:
            score += 5
        
        # Issue responsiveness
        if repo.get('open_issues_count', 0) < 50:
            score += 10
        elif repo.get('open_issues_count', 0) < 100:
            score += 5
        
        return min(score, 100)
    
    def _determine_contribution_status(self, repo: Dict, score: float, 
                                     commits: List, has_contributing: bool) -> ContributionStatus:
        """Determine the contribution status based on analysis"""
        
        if repo.get('archived', False):
            return ContributionStatus.ARCHIVED_INACTIVE
        
        if len(commits) == 0:
            return ContributionStatus.ARCHIVED_INACTIVE
        
        if score >= 70:
            return ContributionStatus.ACTIVELY_ACCEPTING
        elif score >= 40:
            return ContributionStatus.LIMITED_SCOPE
        else:
            return ContributionStatus.NOT_ACCEPTING
    
    def _analyze_tech_stack(self, repo: Dict) -> List[str]:
        """Analyze the technology stack of the repository"""
        tech_stack = []
        
        language = repo.get('language')
        if language:
            tech_stack.append(language)
        
        # Common frameworks and tools based on language
        language_frameworks = {
            'JavaScript': ['Node.js', 'React', 'Vue.js', 'Angular'],
            'Python': ['Django', 'Flask', 'FastAPI', 'Pandas'],
            'Java': ['Spring', 'Maven', 'Gradle'],
            'C#': ['.NET', 'ASP.NET'],
            'Go': ['Gin', 'Echo'],
            'Rust': ['Cargo', 'Actix'],
            'TypeScript': ['Angular', 'React', 'Node.js']
        }
        
        if language in language_frameworks:
            # This would ideally check package files or README for actual frameworks
            tech_stack.extend(language_frameworks[language][:2])  # Add first 2 as examples
        
        return tech_stack
    
    def _estimate_response_time(self, commits: List, issues: List) -> str:
        """Estimate response time based on activity"""
        if len(commits) > 20:
            return "Within 1-3 days"
        elif len(commits) > 10:
            return "Within 1 week"
        elif len(commits) > 0:
            return "Within 2-4 weeks"
        else:
            return "Slow or no response"
    
    def _assess_setup_complexity(self, repo: Dict, tech_stack: List[str]) -> str:
        """Assess the complexity of setting up the project"""
        complexity_indicators = 0
        
        # Multiple languages/frameworks increase complexity
        if len(tech_stack) > 3:
            complexity_indicators += 1
        
        # Large repositories are typically more complex
        if repo.get('size', 0) > 10000:  # KB
            complexity_indicators += 1
        
        # Many dependencies (estimated)
        if repo.get('language') in ['JavaScript', 'Python', 'Java']:
            complexity_indicators += 1
        
        if complexity_indicators == 0:
            return "Simple"
        elif complexity_indicators <= 2:
            return "Moderate"
        else:
            return "Complex"
    
    def _analyze_maintainer_activity(self, commits: List, contributors: List) -> str:
        """Analyze maintainer activity level"""
        if len(commits) > 30:
            return "Very Active"
        elif len(commits) > 15:
            return "Active"
        elif len(commits) > 5:
            return "Moderately Active"
        elif len(commits) > 0:
            return "Low Activity"
        else:
            return "Inactive"
    
    def _parse_datetime(self, date_str: str) -> datetime:
        """Safely parse datetime string"""
        try:
            if date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                return datetime.now()
        except ValueError:
            return datetime.now()
