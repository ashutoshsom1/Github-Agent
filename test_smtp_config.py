#!/usr/bin/env python3
"""
Enhanced email configuration test for corporate accounts
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

def test_smtp_configurations():
    """Test different SMTP configurations for corporate Office 365"""
    
    load_dotenv()
    
    email_user = os.getenv('EMAIL_USER')
    # email_user = "name@company.com"
    email_password = os.getenv('EMAIL_PASSWORD')
    
    if not email_user or not email_password:
        print("❌ EMAIL_USER or EMAIL_PASSWORD not found in .env file")
        return False
    
    # Different SMTP configurations to try
    smtp_configs = [
        {
            'name': 'Office 365 (recommended for corporate)',
            'host': 'smtp.office365.com',
            'port': 587,
            'use_tls': True
        },
        {
            'name': 'Outlook.com (alternative)',
            'host': 'smtp-mail.outlook.com',
            'port': 587,
            'use_tls': True
        },
        {
            'name': 'Office 365 with SSL',
            'host': 'smtp.office365.com',
            'port': 465,
            'use_tls': False,
            'use_ssl': True
        }
    ]
    
    print(f"🧪 Testing SMTP configurations for: {email_user}")
    print("=" * 60)
    
    for i, config in enumerate(smtp_configs, 1):
        print(f"\n📧 Test {i}: {config['name']}")
        print(f"   Host: {config['host']}")
        print(f"   Port: {config['port']}")
        
        try:
            if config.get('use_ssl'):
                server = smtplib.SMTP_SSL(config['host'], config['port'])
            else:
                server = smtplib.SMTP(config['host'], config['port'])
            
            if config.get('use_tls'):
                server.starttls()
            
            print("   🔐 Attempting authentication...")
            server.login(email_user, email_password)
            
            print("   ✅ Authentication successful!")
            
            # Create test email
            msg = MIMEMultipart()
            msg['From'] = email_user
            msg['To'] = email_user
            msg['Subject'] = "GitHub Agent Test Email - Configuration Test"
            
            body = f"""
            <html>
            <body>
                <h2>🎉 SMTP Configuration Test Successful!</h2>
                <p>This email confirms that your SMTP configuration is working correctly.</p>
                <p><strong>Configuration used:</strong></p>
                <ul>
                    <li>Host: {config['host']}</li>
                    <li>Port: {config['port']}</li>
                    <li>TLS: {config.get('use_tls', False)}</li>
                    <li>SSL: {config.get('use_ssl', False)}</li>
                </ul>
                <p>You can now use the GitHub Repository Analysis Agent!</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))
            
            print("   📤 Sending test email...")
            server.sendmail(email_user, email_user, msg.as_string())
            server.quit()
            
            print(f"   🎉 SUCCESS! Email sent using {config['name']}")
            print(f"   💡 Update your .env file with these settings:")
            print(f"      EMAIL_HOST={config['host']}")
            print(f"      EMAIL_PORT={config['port']}")
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"   ❌ Authentication failed: {e}")
            print(f"   💡 This configuration doesn't work with your credentials")
            
        except smtplib.SMTPConnectError as e:
            print(f"   ❌ Connection failed: {e}")
            print(f"   💡 Cannot connect to {config['host']}:{config['port']}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        finally:
            try:
                server.quit()
            except:
                pass
    
    print("\n" + "=" * 60)
    print("❌ All SMTP configurations failed!")
    print("\n💡 Additional troubleshooting steps:")
    print("1. Check if your corporate email requires App Passwords")
    print("2. Contact your IT department for SMTP settings")
    print("3. Try enabling 'Less Secure Apps' if available")
    print("4. Check if your firewall blocks SMTP ports")
    
    return False

def main():
    """Main function"""
    print("🔧 GitHub Agent - SMTP Configuration Test")
    print("=" * 60)
    
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        return
    
    success = test_smtp_configurations()
    
    if success:
        print("\n🎉 Email configuration test PASSED!")
        print("You can now run: python test_email.py")
    else:
        print("\n❌ Email configuration test FAILED!")
        print("Please contact your IT department for assistance.")

if __name__ == "__main__":
    main()
