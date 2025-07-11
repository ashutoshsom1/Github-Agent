import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import zipfile
import os
import sys
from typing import Dict, List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config.settings import settings

class EmailSender:
    def __init__(self):
        self.smtp_host = settings.email_host
        self.smtp_port = settings.email_port
        self.username = settings.email_user
        self.password = settings.email_password
        self.use_tls = settings.email_use_tls
    
    async def send_reports(self, reports: Dict, recipient_email: str) -> bool:
        """Send the generated reports via email"""
        try:
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = recipient_email
            msg['Subject'] = f"GitHub Repository Analysis Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create email body
            email_body = self._create_email_body(reports)
            msg.attach(MIMEText(email_body, 'html'))
            
            # Create attachments
            attachment_path = self._create_attachments(reports)
            if attachment_path:
                self._attach_file(msg, attachment_path)
            
            # Send email
            await self._send_email(msg, recipient_email)
            
            # Cleanup
            if attachment_path and os.path.exists(attachment_path):
                os.remove(attachment_path)
            
            print(f"✅ Reports successfully sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {str(e)}")
            return False
    
    def _create_email_body(self, reports: Dict) -> str:
        """Create the main email body"""
        total_repos = reports['total_repositories']
        generated_at = reports['generated_at']
        
        # Count repositories by status
        status_counts = {}
        for report in reports['individual_reports']:
            status = report['data']['repository'].contribution_status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        actively_accepting = status_counts.get('actively_accepting', 0)
        limited_scope = status_counts.get('limited_scope', 0)
        not_accepting = status_counts.get('not_accepting', 0)
        archived = status_counts.get('archived_inactive', 0)
        
        # Get top repositories
        top_repos = sorted(
            reports['individual_reports'], 
            key=lambda x: x['data']['repository'].contribution_score, 
            reverse=True
        )[:5]
        
        email_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .summary {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; min-width: 120px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #667eea; }}
                .metric-label {{ font-size: 12px; color: #666; text-transform: uppercase; }}
                .status-badge {{ padding: 5px 12px; border-radius: 20px; color: white; font-weight: bold; font-size: 12px; }}
                .actively-accepting {{ background: #28a745; }}
                .limited-scope {{ background: #ffc107; color: black; }}
                .not-accepting {{ background: #dc3545; }}
                .archived-inactive {{ background: #6c757d; }}
                .repo-item {{ background: white; margin: 10px 0; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .repo-name {{ font-weight: bold; color: #667eea; }}
                .repo-score {{ float: right; background: #e9ecef; padding: 5px 10px; border-radius: 15px; font-size: 12px; }}
                .footer {{ background: #f8f9fa; padding: 20px; margin-top: 30px; text-align: center; border-radius: 8px; }}
                .cta-button {{ background: #667eea; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔍 GitHub Repository Analysis Report</h1>
                <p>Comprehensive analysis of open source contribution opportunities</p>
                <p><strong>Generated:</strong> {datetime.fromisoformat(generated_at).strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="summary">
                <h2>📊 Analysis Summary</h2>
                <div class="metric">
                    <div class="metric-value">{total_repos}</div>
                    <div class="metric-label">Total Repositories</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #28a745;">{actively_accepting}</div>
                    <div class="metric-label">Actively Accepting</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #ffc107;">{limited_scope}</div>
                    <div class="metric-label">Limited Scope</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #dc3545;">{not_accepting}</div>
                    <div class="metric-label">Not Accepting</div>
                </div>
                <div class="metric">
                    <div class="metric-value" style="color: #6c757d;">{archived}</div>
                    <div class="metric-label">Archived/Inactive</div>
                </div>
            </div>
            
            <div style="margin: 30px 0;">
                <h2>⭐ Top Contribution Opportunities</h2>
                {''.join([self._format_repo_item(repo) for repo in top_repos])}
            </div>
            
            <div class="footer">
                <h3>📎 Detailed Reports Attached</h3>
                <p>Individual reports for each repository are attached as a ZIP file.</p>
                <p>Each report contains:</p>
                <ul style="text-align: left; display: inline-block;">
                    <li>Detailed contribution analysis</li>
                    <li>Getting started guide</li>
                    <li>Technical requirements</li>
                    <li>Maintainer activity insights</li>
                    <li>Specific recommendations</li>
                </ul>
                
                <div style="margin-top: 20px;">
                    <p><em>Happy contributing! 🚀</em></p>
                    <p style="font-size: 12px; color: #666;">
                        This report was generated by GitHub Repository Analysis Agent
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return email_body
    
    def _format_repo_item(self, repo_report: Dict) -> str:
        """Format a repository item for the email"""
        repo = repo_report['data']['repository']
        status_class = repo.contribution_status.value.replace("_", "-")
        
        return f"""
        <div class="repo-item">
            <div class="repo-score">Score: {repo.contribution_score}/100</div>
            <div class="repo-name">{repo.full_name}</div>
            <span class="status-badge {status_class}">
                {repo.contribution_status.value.replace("_", " ").title()}
            </span>
            <p style="margin: 10px 0; color: #666;">{repo.description[:100]}{'...' if len(repo.description) > 100 else ''}</p>
            <div style="font-size: 12px; color: #888;">
                ⭐ {repo.stars:,} stars • 🍴 {repo.forks:,} forks • 
                💻 {repo.language} • 🎯 {repo.good_first_issues} good first issues
            </div>
        </div>
        """
    
    def _create_attachments(self, reports: Dict) -> str:
        """Create ZIP file with all individual reports"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"github_analysis_reports_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w') as zipf:
                # Add summary report
                summary_filename = f"summary_report_{timestamp}.html"
                with open(summary_filename, 'w', encoding='utf-8') as f:
                    f.write(reports['summary'])
                zipf.write(summary_filename)
                os.remove(summary_filename)
                
                # Add individual reports
                for i, report in enumerate(reports['individual_reports']):
                    repo_name = report['repository_name'].replace('/', '_')
                    filename = f"{i+1:02d}_{repo_name}_report.html"
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(report['html_content'])
                    zipf.write(filename)
                    os.remove(filename)
            
            return zip_filename
            
        except Exception as e:
            print(f"❌ Failed to create attachments: {str(e)}")
            return None
    
    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach file to email message"""
        with open(file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(file_path)}'
        )
        msg.attach(part)
    
    async def _send_email(self, msg: MIMEMultipart, recipient_email: str):
        """Send the email message"""
        server = smtplib.SMTP(self.smtp_host, self.smtp_port)
        
        if self.use_tls:
            server.starttls()
        
        server.login(self.username, self.password)
        text = msg.as_string()
        server.sendmail(self.username, recipient_email, text)
        server.quit()
