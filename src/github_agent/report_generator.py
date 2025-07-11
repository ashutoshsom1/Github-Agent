from typing import List, Dict
from datetime import datetime
import json
from jinja2 import Template
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from github_agent.analyzer import RepositoryAnalysis, ContributionStatus

class ReportGenerator:
    def __init__(self):
        self.template = self._get_report_template()
    
    def generate_reports(self, analyses: List[RepositoryAnalysis]) -> Dict:
        """Generate comprehensive reports for all analyzed repositories"""
        
        # Categorize repositories
        categorized = self._categorize_repositories(analyses)
        
        # Generate summary report
        summary_report = self._generate_summary_report(analyses, categorized)
        
        # Generate individual reports
        individual_reports = []
        for analysis in analyses:
            individual_report = self._generate_individual_report(analysis)
            individual_reports.append(individual_report)
        
        return {
            "summary": summary_report,
            "individual_reports": individual_reports,
            "total_repositories": len(analyses),
            "generated_at": datetime.now().isoformat()
        }
    
    def _categorize_repositories(self, analyses: List[RepositoryAnalysis]) -> Dict:
        """Categorize repositories by contribution status"""
        categorized = {
            "actively_accepting": [],
            "limited_scope": [],
            "not_accepting": [],
            "archived_inactive": []
        }
        
        for analysis in analyses:
            status_key = analysis.contribution_status.value
            categorized[status_key].append(analysis)
        
        return categorized
    
    def _generate_summary_report(self, analyses: List[RepositoryAnalysis], categorized: Dict) -> str:
        """Generate a summary report of all repositories"""
        
        # Calculate statistics
        total = len(analyses)
        actively_accepting = len(categorized["actively_accepting"])
        limited_scope = len(categorized["limited_scope"])
        not_accepting = len(categorized["not_accepting"])
        archived = len(categorized["archived_inactive"])
        
        # Top repositories by contribution score
        top_repos = sorted(analyses, key=lambda x: x.contribution_score, reverse=True)[:10]
        
        # Most popular languages
        languages = {}
        for analysis in analyses:
            lang = analysis.language
            languages[lang] = languages.get(lang, 0) + 1
        
        popular_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        
        summary_data = {
            "total_repositories": total,
            "actively_accepting": actively_accepting,
            "actively_accepting_pct": (actively_accepting / total * 100) if total > 0 else 0,
            "limited_scope": limited_scope,
            "limited_scope_pct": (limited_scope / total * 100) if total > 0 else 0,
            "not_accepting": not_accepting,
            "not_accepting_pct": (not_accepting / total * 100) if total > 0 else 0,
            "archived": archived,
            "archived_pct": (archived / total * 100) if total > 0 else 0,
            "top_repositories": top_repos,
            "popular_languages": popular_languages,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return self._render_summary_template(summary_data)
    
    def _generate_individual_report(self, analysis: RepositoryAnalysis) -> Dict:
        """Generate a detailed report for a single repository"""
        
        # Contribution recommendations
        recommendations = self._generate_recommendations(analysis)
        
        # Getting started guide
        getting_started = self._generate_getting_started_guide(analysis)
        
        report_data = {
            "repository": analysis,
            "recommendations": recommendations,
            "getting_started": getting_started,
            "contribution_indicators": self._get_contribution_indicators(analysis),
            "technical_details": self._get_technical_details(analysis),
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return {
            "repository_name": analysis.full_name,
            "html_content": self._render_individual_template(report_data),
            "data": report_data
        }
    
    def _generate_recommendations(self, analysis: RepositoryAnalysis) -> List[str]:
        """Generate recommendations based on repository analysis"""
        recommendations = []
        
        if analysis.contribution_status == ContributionStatus.ACTIVELY_ACCEPTING:
            recommendations.append("✅ This repository is actively accepting contributions!")
            
            if analysis.good_first_issues > 0:
                recommendations.append(f"🎯 Start with {analysis.good_first_issues} 'good-first-issue' labeled issues")
            
            if analysis.help_wanted_issues > 0:
                recommendations.append(f"🆘 {analysis.help_wanted_issues} issues are specifically seeking help")
            
            if analysis.has_contributing_guide:
                recommendations.append("📖 Read the CONTRIBUTING.md file before starting")
            else:
                recommendations.append("⚠️ No contribution guide found - reach out to maintainers first")
        
        elif analysis.contribution_status == ContributionStatus.LIMITED_SCOPE:
            recommendations.append("⚠️ This repository has limited contribution opportunities")
            recommendations.append("💡 Consider small bug fixes or documentation improvements")
            
        elif analysis.contribution_status == ContributionStatus.NOT_ACCEPTING:
            recommendations.append("❌ This repository doesn't appear to be accepting contributions")
            recommendations.append("👀 Consider forking for your own modifications")
            
        else:  # ARCHIVED_INACTIVE
            recommendations.append("🗄️ This repository is archived or inactive")
            recommendations.append("🔍 Look for active forks or alternatives")
        
        # Technical recommendations
        if analysis.setup_complexity == "Complex":
            recommendations.append("🔧 Complex setup - allocate extra time for environment configuration")
        
        if analysis.response_time_estimate == "Slow or no response":
            recommendations.append("⏰ Maintainers may be slow to respond - be patient")
        
        return recommendations
    
    def _generate_getting_started_guide(self, analysis: RepositoryAnalysis) -> List[str]:
        """Generate a getting started guide"""
        steps = [
            f"1. Fork the repository: {analysis.url}",
            "2. Clone your fork locally",
            f"3. Set up the {analysis.language} development environment"
        ]
        
        if analysis.tech_stack:
            tech_list = ", ".join(analysis.tech_stack)
            steps.append(f"4. Install dependencies for: {tech_list}")
        
        if analysis.has_contributing_guide:
            steps.append("5. Read CONTRIBUTING.md for specific guidelines")
        
        if analysis.good_first_issues > 0:
            steps.append("6. Browse 'good-first-issue' labeled issues")
        else:
            steps.append("6. Look for open issues or documentation improvements")
        
        steps.extend([
            "7. Create a feature branch for your changes",
            "8. Make your changes and add tests if applicable",
            "9. Submit a pull request with a clear description"
        ])
        
        return steps
    
    def _get_contribution_indicators(self, analysis: RepositoryAnalysis) -> Dict:
        """Get contribution indicators summary"""
        return {
            "contribution_score": analysis.contribution_score,
            "status": analysis.contribution_status.value.replace("_", " ").title(),
            "has_contributing_guide": analysis.has_contributing_guide,
            "has_code_of_conduct": analysis.has_code_of_conduct,
            "has_issue_templates": analysis.has_issue_templates,
            "has_pr_templates": analysis.has_pr_templates,
            "good_first_issues": analysis.good_first_issues,
            "help_wanted_issues": analysis.help_wanted_issues,
            "response_time": analysis.response_time_estimate
        }
    
    def _get_technical_details(self, analysis: RepositoryAnalysis) -> Dict:
        """Get technical details summary"""
        return {
            "language": analysis.language,
            "tech_stack": analysis.tech_stack,
            "setup_complexity": analysis.setup_complexity,
            "license": analysis.license,
            "stars": analysis.stars,
            "forks": analysis.forks,
            "contributors": analysis.contributors_count,
            "recent_commits": analysis.recent_commits,
            "maintainer_activity": analysis.maintainer_activity
        }
    
    def _get_report_template(self) -> str:
        """Get the HTML template for reports"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>GitHub Repository Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #f4f4f4; padding: 20px; border-radius: 5px; }
        .status-badge { padding: 5px 10px; border-radius: 3px; color: white; font-weight: bold; }
        .actively-accepting { background: #28a745; }
        .limited-scope { background: #ffc107; color: black; }
        .not-accepting { background: #dc3545; }
        .archived-inactive { background: #6c757d; }
        .section { margin: 20px 0; padding: 15px; border-left: 4px solid #007bff; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }
        .recommendation { margin: 5px 0; padding: 10px; background: #e9ecef; border-radius: 3px; }
        .step { margin: 5px 0; padding: 8px; background: #f1f3f4; border-radius: 3px; }
        .tech-tag { display: inline-block; background: #007bff; color: white; padding: 3px 8px; margin: 2px; border-radius: 3px; font-size: 0.8em; }
    </style>
</head>
<body>
    {{ content }}
</body>
</html>
        """
    
    def _render_summary_template(self, data: Dict) -> str:
        """Render summary report template"""
        content = f"""
        <div class="header">
            <h1>🔍 GitHub Repository Analysis Summary</h1>
            <p><strong>Generated:</strong> {data['generated_at']}</p>
            <p><strong>Total Repositories Analyzed:</strong> {data['total_repositories']}</p>
        </div>
        
        <div class="section">
            <h2>📊 Contribution Status Distribution</h2>
            <div class="metric">
                <strong>Actively Accepting:</strong> {data['actively_accepting']} ({data['actively_accepting_pct']:.1f}%)
            </div>
            <div class="metric">
                <strong>Limited Scope:</strong> {data['limited_scope']} ({data['limited_scope_pct']:.1f}%)
            </div>
            <div class="metric">
                <strong>Not Accepting:</strong> {data['not_accepting']} ({data['not_accepting_pct']:.1f}%)
            </div>
            <div class="metric">
                <strong>Archived/Inactive:</strong> {data['archived']} ({data['archived_pct']:.1f}%)
            </div>
        </div>
        
        <div class="section">
            <h2>⭐ Top Repositories by Contribution Score</h2>
            {''.join([f'<div class="recommendation"><strong>{repo.full_name}</strong> - Score: {repo.contribution_score}/100 ({repo.contribution_status.value.replace("_", " ").title()})</div>' for repo in data['top_repositories']])}
        </div>
        
        <div class="section">
            <h2>💻 Popular Programming Languages</h2>
            {''.join([f'<span class="tech-tag">{lang} ({count})</span>' for lang, count in data['popular_languages']])}
        </div>
        """
        
        template = Template(self._get_report_template())
        return template.render(content=content)
    
    def _render_individual_template(self, data: Dict) -> str:
        """Render individual repository report template"""
        repo = data['repository']
        
        status_class = repo.contribution_status.value.replace("_", "-")
        
        content = f"""
        <div class="header">
            <h1>📁 {repo.full_name}</h1>
            <p>{repo.description}</p>
            <span class="status-badge {status_class}">
                {repo.contribution_status.value.replace("_", " ").title()}
            </span>
            <p><strong>Contribution Score:</strong> {repo.contribution_score}/100</p>
        </div>
        
        <div class="section">
            <h2>📈 Repository Metrics</h2>
            <div class="metric"><strong>Stars:</strong> {repo.stars:,}</div>
            <div class="metric"><strong>Forks:</strong> {repo.forks:,}</div>
            <div class="metric"><strong>Open Issues:</strong> {repo.open_issues}</div>
            <div class="metric"><strong>Contributors:</strong> {repo.contributors_count}</div>
            <div class="metric"><strong>Recent Commits:</strong> {repo.recent_commits}</div>
        </div>
        
        <div class="section">
            <h2>🔧 Technical Details</h2>
            <div class="metric"><strong>Language:</strong> {repo.language}</div>
            <div class="metric"><strong>License:</strong> {repo.license or 'Not specified'}</div>
            <div class="metric"><strong>Setup Complexity:</strong> {repo.setup_complexity}</div>
            <div class="metric"><strong>Maintainer Activity:</strong> {repo.maintainer_activity}</div>
            <div>
                <strong>Tech Stack:</strong><br>
                {''.join([f'<span class="tech-tag">{tech}</span>' for tech in repo.tech_stack])}
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Contribution Opportunities</h2>
            <div class="metric"><strong>Good First Issues:</strong> {repo.good_first_issues}</div>
            <div class="metric"><strong>Help Wanted Issues:</strong> {repo.help_wanted_issues}</div>
            <div class="metric"><strong>Expected Response Time:</strong> {repo.response_time_estimate}</div>
            <div class="metric"><strong>Has Contributing Guide:</strong> {'✅' if repo.has_contributing_guide else '❌'}</div>
            <div class="metric"><strong>Has Code of Conduct:</strong> {'✅' if repo.has_code_of_conduct else '❌'}</div>
        </div>
        
        <div class="section">
            <h2>💡 Recommendations</h2>
            {''.join([f'<div class="recommendation">{rec}</div>' for rec in data['recommendations']])}
        </div>
        
        <div class="section">
            <h2>🚀 Getting Started</h2>
            {''.join([f'<div class="step">{step}</div>' for step in data['getting_started']])}
        </div>
        
        <div class="section">
            <h2>🔗 Links</h2>
            <p><a href="{repo.url}" target="_blank">Repository URL</a></p>
            <p><a href="{repo.url}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22" target="_blank">Good First Issues</a></p>
            <p><a href="{repo.url}/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22" target="_blank">Help Wanted Issues</a></p>
        </div>
        """
        
        template = Template(self._get_report_template())
        return template.render(content=content)
