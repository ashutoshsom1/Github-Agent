from .api_client import GitHubAPIClient
from .analyzer import RepositoryAnalyzer
from .report_generator import ReportGenerator
from .email_sender import EmailSender

class GitHubAnalysisAgent:
    def __init__(self):
        self.api_client = GitHubAPIClient()
        self.analyzer = RepositoryAnalyzer()
        self.report_generator = ReportGenerator()
        self.email_sender = EmailSender()
    
    async def analyze_repositories(self, keyword: str, recipient_email: str):
        """Main method to analyze repositories and send reports"""
        print(f"🔍 Searching for repositories with keyword: {keyword}")
        
        # Fetch repositories
        repositories = await self.api_client.search_repositories(keyword)
        
        print(f"📊 Found {len(repositories)} repositories to analyze")
        
        # Analyze each repository
        analyzed_repos = []
        for repo in repositories:
            analysis = await self.analyzer.analyze_repository(repo)
            analyzed_repos.append(analysis)
        
        # Generate reports
        reports = self.report_generator.generate_reports(analyzed_repos)
        
        # Send email with reports
        await self.email_sender.send_reports(reports, recipient_email)
        
        print(f"✅ Analysis complete! Reports sent to {recipient_email}")
        
        return analyzed_repos
