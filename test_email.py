#!/usr/bin/env python3
"""
Test script to verify email functionality
"""

import asyncio
import os
import sys
from datetime import datetime
import tempfile
import zipfile

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from github_agent.email_sender import EmailSender
from github_agent.analyzer import ContributionStatus, RepositoryAnalysis

def create_test_reports():
    """Create mock reports for testing email functionality"""
    
    # Create mock repository analyses
    mock_repo1 = RepositoryAnalysis(
        name="test-repo-1",
        full_name="owner/test-repo-1",
        description="A test repository for machine learning",
        url="https://github.com/owner/test-repo-1",
        stars=1250,
        forks=340,
        language="Python",
        license="MIT",
        contribution_status=ContributionStatus.ACTIVELY_ACCEPTING,
        contribution_score=92.5,
        last_activity=datetime.now(),
        open_issues=15,
        good_first_issues=8,
        help_wanted_issues=5,
        recent_commits=45,
        contributors_count=25,
        has_contributing_guide=True,
        has_code_of_conduct=True,
        has_issue_templates=True,
        has_pr_templates=True,
        response_time_estimate="Within 1-3 days",
        tech_stack=["Python", "TensorFlow", "Scikit-learn"],
        setup_complexity="Moderate",
        maintainer_activity="Very Active"
    )
    
    mock_repo2 = RepositoryAnalysis(
        name="test-repo-2",
        full_name="owner/test-repo-2",
        description="Another test repository for web development",
        url="https://github.com/owner/test-repo-2",
        stars=890,
        forks=156,
        language="JavaScript",
        license="Apache-2.0",
        contribution_status=ContributionStatus.LIMITED_SCOPE,
        contribution_score=68.0,
        last_activity=datetime.now(),
        open_issues=8,
        good_first_issues=3,
        help_wanted_issues=2,
        recent_commits=22,
        contributors_count=12,
        has_contributing_guide=False,
        has_code_of_conduct=True,
        has_issue_templates=False,
        has_pr_templates=False,
        response_time_estimate="Within 1 week",
        tech_stack=["JavaScript", "React", "Node.js"],
        setup_complexity="Simple",
        maintainer_activity="Active"
    )
    
    mock_repo3 = RepositoryAnalysis(
        name="test-repo-3",
        full_name="owner/test-repo-3",
        description="A test repository that's not accepting contributions",
        url="https://github.com/owner/test-repo-3",
        stars=2100,
        forks=445,
        language="Go",
        license=None,
        contribution_status=ContributionStatus.NOT_ACCEPTING,
        contribution_score=25.0,
        last_activity=datetime.now(),
        open_issues=3,
        good_first_issues=0,
        help_wanted_issues=0,
        recent_commits=5,
        contributors_count=3,
        has_contributing_guide=False,
        has_code_of_conduct=False,
        has_issue_templates=False,
        has_pr_templates=False,
        response_time_estimate="Slow or no response",
        tech_stack=["Go"],
        setup_complexity="Complex",
        maintainer_activity="Low Activity"
    )
    
    # Create mock individual reports
    individual_reports = []
    for repo in [mock_repo1, mock_repo2, mock_repo3]:
        report_data = {
            "repository": repo,
            "recommendations": [
                "✅ This is a test recommendation",
                "📖 Read the documentation carefully",
                "🎯 Focus on beginner-friendly issues"
            ],
            "getting_started": [
                "1. Fork the repository",
                "2. Clone your fork locally",
                "3. Set up the development environment",
                "4. Make your changes",
                "5. Submit a pull request"
            ],
            "contribution_indicators": {
                "contribution_score": repo.contribution_score,
                "status": repo.contribution_status.value.replace("_", " ").title(),
                "has_contributing_guide": repo.has_contributing_guide,
                "has_code_of_conduct": repo.has_code_of_conduct,
                "has_issue_templates": repo.has_issue_templates,
                "has_pr_templates": repo.has_pr_templates,
                "good_first_issues": repo.good_first_issues,
                "help_wanted_issues": repo.help_wanted_issues,
                "response_time": repo.response_time_estimate
            },
            "technical_details": {
                "language": repo.language,
                "tech_stack": repo.tech_stack,
                "setup_complexity": repo.setup_complexity,
                "license": repo.license,
                "stars": repo.stars,
                "forks": repo.forks,
                "contributors": repo.contributors_count,
                "recent_commits": repo.recent_commits,
                "maintainer_activity": repo.maintainer_activity
            },
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Create simple HTML content for the report
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Report - {repo.full_name}</title>
        </head>
        <body>
            <h1>📁 {repo.full_name}</h1>
            <p>{repo.description}</p>
            <p><strong>Contribution Score:</strong> {repo.contribution_score}/100</p>
            <p><strong>Status:</strong> {repo.contribution_status.value.replace("_", " ").title()}</p>
            <p><strong>Language:</strong> {repo.language}</p>
            <p><strong>Stars:</strong> {repo.stars:,}</p>
            <p><strong>Good First Issues:</strong> {repo.good_first_issues}</p>
            <p><em>This is a test report generated for email testing purposes.</em></p>
        </body>
        </html>
        """
        
        individual_reports.append({
            "repository_name": repo.full_name,
            "html_content": html_content,
            "data": report_data
        })
    
    # Create summary HTML
    summary_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Summary Report</title>
    </head>
    <body>
        <h1>🔍 Test GitHub Repository Analysis Summary</h1>
        <p><strong>Total Repositories:</strong> 3</p>
        <p><strong>Actively Accepting:</strong> 1</p>
        <p><strong>Limited Scope:</strong> 1</p>
        <p><strong>Not Accepting:</strong> 1</p>
        <p><em>This is a test summary report.</em></p>
    </body>
    </html>
    """
    
    return {
        "summary": summary_html,
        "individual_reports": individual_reports,
        "total_repositories": 3,
        "generated_at": datetime.now().isoformat()
    }

async def test_email_functionality():
    """Test the email sending functionality"""
    print("📧 Testing Email Functionality")
    print("=" * 50)
    
    # Check environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['EMAIL_HOST', 'EMAIL_USER', 'EMAIL_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        print("\nPlease update your .env file with email credentials.")
        return False
    
    print("✅ Environment variables found")
    
    # Create test reports
    print("📊 Creating test reports...")
    test_reports = create_test_reports()
    print("✅ Test reports created")
    
    # Initialize email sender
    print("📨 Initializing email sender...")
    email_sender = EmailSender()
    print("✅ Email sender initialized")
    
    # Get recipient email
    recipient = os.getenv('EMAIL_USER')  # Send to yourself for testing
    print(f"📮 Email from .env file: '{recipient}'")
    print(f"📮 Email length: {len(recipient) if recipient else 'None'}")
    print(f"📮 Sending test email to: {recipient}")
    
    # Send test email
    try:
        success = await email_sender.send_reports(test_reports, recipient)
        
        if success:
            print("🎉 EMAIL TEST SUCCESSFUL!")
            print(f"✅ Test email sent successfully to {recipient}")
            print("\nCheck your inbox for:")
            print("  • HTML email with repository analysis summary")
            print("  • ZIP attachment with individual reports")
            print("  • Professional formatting and styling")
            return True
        else:
            print("❌ EMAIL TEST FAILED!")
            print("The email could not be sent. Check your email configuration.")
            return False
            
    except Exception as e:
        print(f"❌ EMAIL TEST FAILED with error: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Check your email credentials in .env file")
        print("2. For Gmail, use an App Password (not your regular password)")
        print("3. For Outlook, ensure you have the correct SMTP settings")
        print("4. Check if 2FA is enabled and configured properly")
        return False

def main():
    """Main function"""
    print("🧪 GitHub Repository Analysis Agent - Email Test")
    print("=" * 60)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your email configuration.")
        print("Use .env.example as a template.")
        return
    
    # Run the test
    result = asyncio.run(test_email_functionality())
    
    print("\n" + "=" * 60)
    if result:
        print("🎉 Email functionality is working correctly!")
        print("You can now run the full GitHub analysis with confidence.")
    else:
        print("❌ Email functionality needs to be fixed before proceeding.")
        print("Please check your email configuration and try again.")

if __name__ == "__main__":
    main()
