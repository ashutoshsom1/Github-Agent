#!/usr/bin/env python3
"""
Test script to verify the GitHub Repository Analysis Agent installation
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        # Add src to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
        
        # Test basic imports
        import requests
        print("✅ requests")
        
        import aiohttp
        print("✅ aiohttp")
        
        import jinja2
        print("✅ jinja2")
        
        import click
        print("✅ click")
        
        import rich
        print("✅ rich")
        
        # Test our modules
        from config.settings import settings
        print("✅ settings")
        
        from github_agent.api_client import GitHubAPIClient
        print("✅ GitHubAPIClient")
        
        from github_agent.analyzer import RepositoryAnalyzer
        print("✅ RepositoryAnalyzer")
        
        from github_agent.report_generator import ReportGenerator
        print("✅ ReportGenerator")
        
        from github_agent.email_sender import EmailSender
        print("✅ EmailSender")
        
        from github_agent import GitHubAnalysisAgent
        print("✅ GitHubAnalysisAgent")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_environment():
    """Test if environment variables are configured"""
    print("\n🔧 Testing environment configuration...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("⚠️  .env file not found")
        print("   Create one based on .env.example")
        return False
    
    # Check required environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    required_vars = ['GITHUB_TOKEN', 'EMAIL_HOST', 'EMAIL_USER', 'EMAIL_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   • {var}")
        return False
    
    print("✅ Environment configuration looks good!")
    return True

def main():
    """Run all tests"""
    print("🧪 GitHub Repository Analysis Agent - Installation Test\n")
    
    imports_ok = test_imports()
    env_ok = test_environment()
    
    print("\n" + "="*50)
    
    if imports_ok and env_ok:
        print("🎉 Installation test PASSED!")
        print("You're ready to run the GitHub Repository Analysis Agent!")
        print("\nNext steps:")
        print("1. Run: python main.py --keyword 'your-keyword' --email 'your-email'")
        print("2. Or check example.py for Python API usage")
    else:
        print("❌ Installation test FAILED!")
        print("Please fix the issues above before proceeding.")
        
        if not imports_ok:
            print("\nTo fix import issues:")
            print("  pip install -r requirements.txt")
        
        if not env_ok:
            print("\nTo fix environment issues:")
            print("  1. Copy .env.example to .env")
            print("  2. Fill in your GitHub token and email credentials")

if __name__ == "__main__":
    main()
